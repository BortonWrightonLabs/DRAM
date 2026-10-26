#!/usr/bin/env python
import sys
import re
import pandas as pd


def extract_kegg_orthology(description):
    if pd.isna(description):
        return None
    orthologies = dict.fromkeys(re.findall(r"\bK\d{5}\b", description))
    return "/".join(orthologies) or None


def extract_kegg_EC(description):
    if pd.isna(description):
        return None
    ec_fields = re.findall(r"\[EC:([^\]]*)\]", description)
    if not ec_fields:
        return None
    ec_numbers = dict.fromkeys(
        number
        for field in ec_fields
        for number in re.findall(r"\b\d+\.\d+\.\d+\.\d+\b", field)
    )
    return "; ".join(f"EC:{number}" for number in ec_numbers)


def assign_rank(row, a_rank, b_rank, db_name_bit_score):
    """Assign rank based on bit score and provided thresholds."""
    if pd.isna(row[db_name_bit_score]):
        return None
    elif row[db_name_bit_score] >= a_rank:
        return "A"
    elif row[db_name_bit_score] >= b_rank:
        return "B"
    else:
        return None


def main(
    input_fasta,
    db_name,
    descriptions_path,
    bit_score_threshold,
    gene_locs_path,
    raw_mmseqs_path,
    output_path,
):
    print(f"Starting processing for input_fasta: {input_fasta}, database: {db_name}")

    print(f"Loading MMseqs output from {raw_mmseqs_path}")

    df_gene_locs = pd.read_csv(
        gene_locs_path,
        sep="\t",
        usecols=["query_id", "start_position", "stop_position"],
    )
    print("Gene locations loaded. Sample rows:")
    print(df_gene_locs.head())

    df_mmseqs = pd.read_csv(
        raw_mmseqs_path,
        sep="\t",
        usecols=lambda column: column in {"query", "target", "bits", "theader"},
    )
    if df_mmseqs.empty:
        print("No MMseqs hits. Skipping further processing.")
        return
    df_mmseqs.rename(
        columns={
            "query": "query_id",
            "target": f"{db_name}_id",
            "bits": f"{db_name}_bitScore",
        },
        inplace=True,
    )
    print("MMseqs data loaded and columns renamed. Sample rows:")
    print(df_mmseqs.head())

    df_merged = pd.merge(df_mmseqs, df_gene_locs, on="query_id", how="left")
    print("Merged MMseqs output with gene locations. Sample rows:")
    print(df_merged.head())

    if descriptions_path and descriptions_path != "NULL":
        df_descriptions = pd.read_csv(descriptions_path, sep="\t")
        first_column = df_descriptions.columns[0]
        df_descriptions.rename(columns={first_column: f"{db_name}_id"}, inplace=True)

        # Rename 'definition' to 'description', and prefix it with db_name if it exists
        if "definition" in df_descriptions.columns:
            df_descriptions.rename(
                columns={"definition": f"{db_name}_description"}, inplace=True
            )
        elif "description" in df_descriptions.columns:
            # If 'description' already exists, just prefix it with db_name
            df_descriptions.rename(
                columns={"description": f"{db_name}_description"}, inplace=True
            )

        # Prefix other columns except 'A_rank', 'B_rank', and the first column (already handled)
        df_descriptions = df_descriptions.rename(
            columns={
                col: f"{db_name}_{col}"
                for col in df_descriptions.columns
                if col
                not in ["A_rank", "B_rank", f"{db_name}_id", f"{db_name}_description"]
            }
        )

        # Merge descriptions DataFrame
        df_merged = pd.merge(df_merged, df_descriptions, on=f"{db_name}_id", how="left")

        # Assign ranks based on A_rank and B_rank thresholds, directly using them without db_name prefix
        if "A_rank" in df_descriptions.columns and "B_rank" in df_descriptions.columns:
            db_name_bit_score = f"{db_name}_bitScore"
            df_merged[f"{db_name}_rank"] = df_merged.apply(
                lambda row: assign_rank(
                    row, row["A_rank"], row["B_rank"], db_name_bit_score
                ),
                axis=1,
            )

        # Drop A_rank and B_rank columns as they should not be output
        df_merged.drop(columns=["A_rank", "B_rank"], inplace=True, errors="ignore")

    if "theader" in df_merged.columns:
        description_column = f"{db_name}_description"
        if description_column in df_merged.columns:
            df_merged[description_column] = df_merged[description_column].fillna(
                df_merged["theader"]
            )
        else:
            df_merged[description_column] = df_merged["theader"]
        df_merged.drop(columns="theader", inplace=True)

    description_column = f"{db_name}_description"
    if description_column in df_merged.columns:
        if db_name == "kegg":
            df_merged["kegg_EC"] = df_merged[description_column].apply(extract_kegg_EC)
            df_merged.rename(columns={"kegg_id": "kegg_gene_name"}, inplace=True)
            df_merged["kegg_id"] = df_merged[description_column].apply(
                extract_kegg_orthology
            )
        elif db_name == "merops":
            df_merged["merops_family"] = (
                df_merged[description_column]
                .fillna("")
                .str.findall(r"#(\w*.)#")
                .apply(lambda families: ";".join(families))
            )

    df_merged.to_csv(output_path, index=False)
    print("Merged DataFrame saved to", output_path)


if __name__ == "__main__":
    args = sys.argv[1:]
    try:
        float(args[2])
    except (IndexError, ValueError):
        pass
    else:
        args.insert(2, "NULL")

    input_fasta = args[0]
    db_name = args[1]
    descriptions_path = args[2]
    bit_score_threshold = float(args[3])
    gene_locs_path = args[4]
    raw_mmseqs_path = (
        args[5] if len(args) > 5 else f"mmseqs_out/{input_fasta}___mmseqs_{db_name}.tsv"
    )
    output_path = (
        args[6]
        if len(args) > 6
        else f"mmseqs_out/{input_fasta}___mmseqs_{db_name}_formatted.csv"
    )

    main(
        input_fasta,
        db_name,
        descriptions_path,
        bit_score_threshold,
        gene_locs_path,
        raw_mmseqs_path,
        output_path,
    )
