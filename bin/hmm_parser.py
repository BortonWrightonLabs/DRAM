#!/usr/bin/env python
import re
import pandas as pd
import click
import numpy as np

# query_id is targey name, but this matches our query_name later for merging
# In DRAM1 we had query and target swapped compared to usual HMMER terminology
# (so query_name here was target_id in DRAM1, model_start model_end were target_start target_end in DRAM1, etc.)
HMMSCAN_ALL_COLUMNS = [
    "query_id",
    "target_accession",
    "target_length",
    "query_name",
    "query_accession",
    "query_length",
    "full_evalue",
    "full_bitScore",
    "full_bias",
    "domain_number",
    "domain_count",
    "domain_cevalue",
    "domain_ievalue",
    "domain_bitScore",
    "domain_bias",
    "model_start",
    "model_end",
    "alignment_start",
    "alignment_end",
    "env_start",
    "env_end",
    "accuracy",
    "description",
]
HMMSCAN_COLUMN_TYPES = [
    str,
    str,
    int,
    str,
    str,
    int,
    float,
    float,
    float,
    int,
    int,
    float,
    float,
    float,
    float,
    int,
    int,
    int,
    int,
    int,
    int,
    float,
    str,
]
# Potential Columns to include in the final output if they are in the DataFrame (depends on the HMM info file provided and how things are process)
OUTPUT_COLUMNS = [
    "query_id",
    "start_position",
    "stop_position",
    "strandedness",
    "{db_name}_id",
    "{db_name}_acc",
    "{db_name}_ids",
    "{db_name}_full_bitScore",
    "{db_name}_domain_bitScore",
    "description",
    "{db_name}_EC",
    "{db_name}_score_rank",
]


def parse_hmmsearch_domtblout(file):
    print(file)
    df_lines = []
    for line in open(file):
        if not line.startswith("#"):
            line = line.split()
            line = line[:22] + [" ".join(line[22:])]
            df_lines.append(line)

    column_data = {col: [] for col in HMMSCAN_ALL_COLUMNS}
    for line in df_lines:
        for i, col in enumerate(HMMSCAN_ALL_COLUMNS):
            column_data[col].append(HMMSCAN_COLUMN_TYPES[i](line[i]))

    hmmsearch_frame = pd.DataFrame(column_data)
    accessions = hmmsearch_frame["query_accession"].astype("string").str.strip()
    hmmsearch_frame["query_accession"] = accessions.mask(
        accessions.str.casefold().isin(["na", "n/a", "nan", "none", "null", "<na>"])
        | ~accessions.str.contains(r"[A-Za-z0-9]", na=False)
    )

    # Extract the sign part from the description column to determine strandedness
    hmmsearch_frame["strandedness"] = hmmsearch_frame["description"].apply(
        lambda x: 1 if x.endswith("+") else -1
    )

    return hmmsearch_frame


def sig_scores_row_by_row(df, db_name) -> pd.DataFrame:
    df = df.loc[df["score_type"].isin(["full", "domain"])]
    score = df["full_bitScore"].copy()
    mask = df["score_type"] == "full"
    # Use the mask to update the score Series with domain_bitScore where score_type is "domain"
    score = score.where(mask, other=df["domain_bitScore"]).astype(float)
    score = score.loc[score.notna()]
    df = df.loc[score.index]

    if "threshold" in df.columns:
        # only keep rows where score >= threshold
        df = df.loc[score >= df["threshold"].astype(float)]
    elif "A_rank" in df.columns:
        s_a = df["A_rank"].astype(float)
        if "B_rank" not in df.columns:
            df["B_rank"] = pd.NA
        s_b = df["B_rank"].astype(float)

        conditions = [
            (score >= s_a),
            (score >= s_b),
            # The default covers all other cases
        ]
        choices = ["A", "B"]
        df[f"{db_name}_score_rank"] = np.select(conditions, choices, default=pd.NA)
        df = df.dropna(subset=[f"{db_name}_score_rank"])
    else:
        raise ValueError(
            f"No threshold or A_rank columns found in provided info sheet to determine significant hits for {db_name} hmm DB."
        )
    return df


def get_all_hits(hits, db_name):
    return (
        hits.drop_duplicates(subset=["query_id", f"{db_name}_id"])
        .groupby("query_id")[f"{db_name}_id"]
        .agg("; ".join)
    )


def extract_ec_numbers(definition):
    """
    Extract EC numbers from the definition string and format them into a semi-colon separated list.
    Each EC number is prefixed with 'EC:'.
    """
    # This regex pattern looks for EC numbers within square brackets and captures the numbers following "EC:"
    ec_numbers = re.findall(r"\[EC:(.*?)\]", definition)
    # Join the EC numbers with semi-colon separator and prepend 'EC:' to each number
    formatted_ec_numbers = "; ".join(
        [f"EC:{ec.strip()}" for ec_block in ec_numbers for ec in ec_block.split()]
    )
    return formatted_ec_numbers


@click.command()
@click.option(
    "--hmm_domtbl",
    type=click.Path(exists=True),
    help="Path to the HMM search results domtblout file.",
)
@click.option(
    "--hmm_info_path",
    type=click.Path(exists=True),
    help="Path to the hmm_info_path file.",
)
@click.option(
    "--ec_from_info",
    is_flag=True,
    help="Extract EC numbers from definitions in info sheet. Can only be used if hmm_info_path is provided.",
)
@click.option(
    "--gene_locs",
    type=click.Path(exists=True),
    help="Path to the gene locations TSV file.",
)
@click.option("--db_name", type=str, help="Name of the HMM database.")
@click.option("--output", type=click.Path(), help="Path to the formatted output file.")
def main(hmm_domtbl, hmm_info_path, ec_from_info, gene_locs, db_name, output):
    hits = parse_hmmsearch_domtblout(hmm_domtbl)

    hits = hits.drop(columns=["description"])
    if hits.empty:
        print("No hits found in the HMM search results.")
        # df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        # df.to_csv(output, index=False)
        return
    # Load gene locations TSV file
    print("Loading gene locations TSV file...")
    gene_locs_df = pd.read_csv(
        gene_locs, sep="\t", usecols=["query_id", "start_position", "stop_position"]
    )

    # Merge hits_df with gene_locs_df
    hits = pd.merge(hits, gene_locs_df, on="query_id", how="left")

    hits["perc_cov"] = (hits["model_end"] - hits["model_start"] + 1) / hits[
        "query_length"
    ]
    hmm_sheet = False
    if hmm_info_path is not None:
        hmm_sheet = True
        try:
            hmm_info = pd.read_csv(hmm_info_path, sep="\t", index_col=0)
        except Exception as e:
            try:
                hmm_info = pd.read_csv(
                    hmm_info_path, sep="\t", index_col=0, on_bad_lines="skip"
                )
            except Exception as e2:
                print(f"Error reading HMM info file: {e}\n{e2}")
                hmm_sheet = False
    if hmm_sheet and not hmm_info.empty:
        merge_cols = [
            "score_type",
            "threshold",
            f"{db_name}_EC",
            "description",
            "A_rank",
            "B_rank",
        ]
        raise_on_ec = False
        if "description" in hmm_info.columns:
            pass
        elif "definition" in hmm_info.columns:
            hmm_info = hmm_info.rename(columns={"definition": "description"})
        elif (
            pd.api.types.is_string_dtype(hmm_info.iloc[:, -1])
            and hmm_info.columns[-1] not in merge_cols
        ):  # don't need to worry about description in merge cols, cause already checked
            hmm_info["description"] = hmm_info[hmm_info.columns[-1]].copy()
        else:
            raise_on_ec = True

        if ec_from_info:
            if raise_on_ec:
                raise ValueError(
                    "No suitable column found for descriptions in hmm_info_path."
                )
            hmm_info[f"{db_name}_EC"] = hmm_info["description"].apply(
                extract_ec_numbers
            )

        merge_cols = [col for col in merge_cols if col in hmm_info.columns]
        print(hmm_info.columns)
        print(hmm_info)
        hits = hits.merge(
            hmm_info[merge_cols], how="left", left_on="query_name", right_index=True
        )
        hits["score_type"] = hits["score_type"].fillna("full")
        for col in merge_cols:
            if col in ["threshold", "A_rank", "B_rank"]:
                hits[col] = hits[col].fillna(0)
        print(hits.columns)
        print(hits)
        hits_sig = sig_scores_row_by_row(hits, db_name=db_name)
        drop_cols = [
            col
            for col in merge_cols
            if col in hits_sig.columns
            and col
            not in [
                f"{db_name}_EC",
                "description",
            ]
        ]
        hits_sig = hits_sig.drop(columns=drop_cols)
    else:
        hits_sig = hits[hits["perc_cov"] >= 0.35]

    if len(hits_sig) == 0:
        # if nothing significant then return nothing, don't get descriptions
        # df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        # df.to_csv(output, index=False)
        print(f"No significant hits founds for {hmm_domtbl}")
        return

    hits_sig[f"{db_name}_id"] = hits_sig["query_name"].str.replace(
        r".hmm", "", regex=True
    )
    all_hits_sig = get_all_hits(hits_sig, db_name)
    all_hits_sig.name = f"{db_name}_ids"
    hits_sig = hits_sig.merge(
        all_hits_sig, how="left", left_on="query_id", right_index=True
    )

    # Get the best hit
    # hits_sig = hits_sig.sort_values(['full_evalue', "domain_ievalue", "perc_cov"], ascending=[True, True, False]).drop_duplicates(subset=["query_id"])
    hits_sig = hits_sig.sort_values(
        ["full_evalue", "perc_cov"], ascending=[True, False]
    ).drop_duplicates(subset=["query_id"])
    hits_sig = hits_sig.rename(
        columns={
            "query_accession": f"{db_name}_acc",
            "full_bitScore": f"{db_name}_full_bitScore",
            "domain_bitScore": f"{db_name}_domain_bitScore",
        }
    )

    final_cols = [
        col
        for col in [col.format(db_name=db_name) for col in OUTPUT_COLUMNS]
        if col in hits_sig.columns
    ]
    hits_sig = hits_sig[final_cols]

    # Save the modified DataFrame to CSV
    hits_sig.to_csv(output, index=False)


if __name__ == "__main__":
    main()
