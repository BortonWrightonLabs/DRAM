#!/usr/bin/env python
import os
from pathlib import Path

import click
import polars as pl
from skbio.io import read as read_sequence

from utils.logger import get_logger

FASTA_COLUMN = os.getenv("FASTA_COLUMN", "input_fasta")

logger = get_logger(filename=Path(__file__).stem)


def read_and_preprocess(
    path: Path, input_fasta: str, seperator=","
) -> pl.LazyFrame | None:
    # We design input fastas from intermediate steps to be named like:
    # "input_fasta___some_information_annotation_file.tsv"
    # input_fasta = input_fasta_from_filepath(path)
    try:
        lf = pl.scan_csv(path, separator=seperator).with_columns(
            pl.lit(input_fasta).alias(FASTA_COLUMN)
        )
        # Validate here so we can log file-specific parse failures before the final collect.
        lf.collect_schema()
        return lf
    except Exception as e:
        logger.error(f"Error loading DataFrame for input_fasta {input_fasta}: {str(e)}")
        return None


def input_fasta_from_filepath(file_path: Path, splitter="___") -> str:
    return file_path.stem.split(splitter)[0]


def bit_score_expr(column_name: str) -> pl.Expr:
    return pl.col(column_name).fill_null(0)


def assign_rank_expr(columns: list[str]) -> pl.Expr:
    kegg_score = (
        bit_score_expr("kegg_bitScore") if "kegg_bitScore" in columns else pl.lit(0)
    )
    uniref_score = (
        bit_score_expr("uniref_bitScore") if "uniref_bitScore" in columns else pl.lit(0)
    )
    motif_checks = [
        bit_score_expr(f"{db}_bitScore") > 60
        for db in ["pfam", "dbcan", "merops"]
        if f"{db}_bitScore" in columns
    ]
    motif_expr = pl.any_horizontal(motif_checks) if motif_checks else pl.lit(False)

    return (
        pl.when(kegg_score > 350)
        .then(pl.lit("A"))
        .when(uniref_score > 350)
        .then(pl.lit("B"))
        .when((kegg_score > 60) | (uniref_score > 60))
        .then(pl.lit("C"))
        .when(motif_expr)
        .then(pl.lit("D"))
        .otherwise(pl.lit("E"))
        .alias("rank")
    )


def convert_bit_scores_to_numeric(lf: pl.LazyFrame) -> pl.LazyFrame:
    bit_score_columns = [
        col for col in lf.collect_schema().names() if "_bitScore" in col
    ]
    if not bit_score_columns:
        return lf
    return lf.with_columns(
        [
            pl.col(col).cast(pl.Float64, strict=False).alias(col)
            for col in bit_score_columns
        ]
    )


def input_fasta_from_genes_path(gene_faa) -> str:
    return Path(gene_faa).stem.split("_called_genes")[0]


# Genes are keyed on (input_fasta, query_id): query_id alone is not unique across
# genomes, because per-sample assemblers reuse contig names (MEGAHIT k141_*).
def count_motifs(gene_faa, motif="(C..CH)", genes_faa_dict=None):
    if genes_faa_dict is None:
        genes_faa_dict = dict()
    input_fasta_name = input_fasta_from_genes_path(gene_faa)
    for seq in read_sequence(gene_faa, format="fasta"):
        key = (input_fasta_name, seq.metadata["id"])
        genes_faa_dict.setdefault(key, {})["heme_regulatory_motif_count"] = len(
            list(seq.find_with_regex(motif))
        )
    return genes_faa_dict


def set_gene_data(gene_faa, genes_faa_dict=None):
    if genes_faa_dict is None:
        genes_faa_dict = dict()
    input_fasta_name = input_fasta_from_genes_path(gene_faa)
    for seq in read_sequence(gene_faa, format="fasta"):
        gene = genes_faa_dict.setdefault((input_fasta_name, seq.metadata["id"]), {})

        split_label = seq.metadata["id"].split("_")
        gene_position = split_label[-1]
        start_position, end_position, strandedness = seq.metadata["description"].split(
            "#"
        )[1:4]

        gene["scaffold"] = (
            seq.metadata["id"]
            .removeprefix(input_fasta_name)
            .removeprefix("_")
            .removesuffix(f"_{gene_position}")
        )
        gene["gene_number"] = int(gene_position)
        gene["start_position"] = int(start_position)
        gene["stop_position"] = int(end_position)
        gene["strandedness"] = int(strandedness)
    return genes_faa_dict


def genes_dict_to_frame(genes_faa_dict: dict) -> pl.DataFrame:
    rows = []
    for (input_fasta, query_id), values in genes_faa_dict.items():
        row = {"query_id": query_id, FASTA_COLUMN: input_fasta}
        row.update(values)
        rows.append(row)
    return (
        pl.DataFrame(rows)
        if rows
        else pl.DataFrame(schema={"query_id": pl.String, FASTA_COLUMN: pl.String})
    )


def organize_columns(df: pl.DataFrame, special_columns=None) -> pl.DataFrame:
    if special_columns is None:
        special_columns = []
    base_columns = [
        "query_id",
        FASTA_COLUMN,
        "scaffold",
        "gene_number",
        "start_position",
        "stop_position",
        "strandedness",
        "rank",
    ]
    base_columns = [col for col in base_columns if col in df.columns]

    kegg_columns = sorted(
        [col for col in df.columns if col.startswith("kegg_")],
        key=lambda x: (x != "kegg_id", x),
    )
    other_columns = [
        col
        for col in df.columns
        if col not in base_columns + kegg_columns + special_columns
    ]

    db_prefixes = sorted(set(col.split("_")[0] for col in other_columns))
    sorted_other_columns = []
    for prefix in db_prefixes:
        prefixed_columns = sorted(
            [col for col in other_columns if col.startswith(prefix + "_")],
            key=lambda x: (x != f"{prefix}_id", x),
        )
        sorted_other_columns.extend(prefixed_columns)

    final_columns_order = (
        base_columns + kegg_columns + sorted_other_columns + special_columns
    )
    return df.select(final_columns_order)


@click.command()
@click.option("--annotations_dir", help="Directory of annotation files")
@click.option("--genes_dir", help="Directory genes faa file paths from prodigal")
@click.option(
    "--dbcan_dir",
    help="Directory of run_dbcan hmm_results.tsv and sub_hmm_results.tsv",
)
@click.option("--output", help="Output file path for the combined annotations.")
def combine_annotations(annotations_dir, genes_dir, dbcan_dir, output):
    """Combine annotation files with ranks and avoid duplicating specific columns."""
    annotations = sorted(Path(annotations_dir).glob("*")) if annotations_dir else []
    genes_faa = sorted(Path(genes_dir).glob("*")) if genes_dir else []
    dbcan_paths = (
        sorted(Path(dbcan_dir).glob("*dbCAN_hmm_results.tsv")) if dbcan_dir else []
    )
    dbcan_sub_paths = (
        sorted(Path(dbcan_dir).glob("*dbCANsub_hmm_results.tsv")) if dbcan_dir else []
    )
    annotation_frames = [
        frame
        for frame in (
            read_and_preprocess(path, input_fasta=input_fasta_from_filepath(path))
            for path in annotations
        )
        if frame is not None
    ]
    if annotation_frames:
        combined_data_lf = pl.concat(annotation_frames, how="diagonal_relaxed")
    else:
        combined_data_lf = pl.LazyFrame(
            schema={"query_id": pl.String, FASTA_COLUMN: pl.String}
        )
    if genes_faa:
        genes_faa_dict = {}
        for gene_path in genes_faa:
            gene_path = str(gene_path)
            count_motifs(gene_path, "(C..CH)", genes_faa_dict=genes_faa_dict)
            set_gene_data(gene_path, genes_faa_dict)
        gene_lf = genes_dict_to_frame(genes_faa_dict).lazy()
        gene_lf_cols = gene_lf.collect_schema().names()
        columns = [col for col in gene_lf_cols if col not in (FASTA_COLUMN, "query_id")]
        combined_data_lf = combined_data_lf.drop(columns, strict=False)
        # Use a full join so genes without hits remain in the output. Join on the
        # genome too: query_id alone is not unique across genomes.
        combined_data_lf = combined_data_lf.join(
            gene_lf, how="full", on=["query_id", FASTA_COLUMN], coalesce=True
        )
    if dbcan_paths:
        dbcan_lf = pl.concat(
            [
                frame
                for frame in (
                    read_and_preprocess(
                        path,
                        input_fasta=input_fasta_from_filepath(path, splitter="_dbCAN"),
                        seperator="\t",
                    )
                    for path in dbcan_paths
                )
                if frame is not None
            ],
            how="diagonal_relaxed",
        )
        dbcan_lf = dbcan_lf.select(
            pl.col(FASTA_COLUMN),
            pl.col("Target Name").alias("query_id"),
            pl.col("HMM Name").str.strip_suffix(".hmm").alias("dbcan_id"),
            pl.col("i-Evalue").alias("dbcan_i_Evalue"),
        )
        combined_data_lf = combined_data_lf.join(
            dbcan_lf, how="full", on=["query_id", FASTA_COLUMN], coalesce=True
        )
    if dbcan_sub_paths:
        dbcan_sub_lf = pl.concat(
            [
                frame
                for frame in (
                    read_and_preprocess(
                        path,
                        input_fasta=input_fasta_from_filepath(path, splitter="_dbCAN"),
                        seperator="\t",
                    )
                    for path in dbcan_sub_paths
                )
                if frame is not None
            ],
            how="diagonal_relaxed",
        )
        dbcan_sub_lf = dbcan_sub_lf.select(
            pl.col(FASTA_COLUMN),
            pl.col("Target Name").alias("query_id"),
            pl.col("Subfam Name").alias("dbcan_sub_id"),
            pl.col("Subfam Composition").alias("dbcan_sub_composition"),
            pl.col("Subfam EC").alias("dbcan_sub_ec"),
            pl.col("Substrate").alias("dbcan_sub_substrate"),
            pl.col("i-Evalue").alias("dbcan_sub_i_Evalue"),
        )
        combined_data_lf = combined_data_lf.join(
            dbcan_sub_lf, how="full", on=["query_id", FASTA_COLUMN], coalesce=True
        )

    combined_data_lf = convert_bit_scores_to_numeric(combined_data_lf)
    all_columns = combined_data_lf.collect_schema().names()
    aggregation_exprs = []
    for col in all_columns:
        if col in ["query_id", FASTA_COLUMN]:
            continue
        if col in ["Completeness", "Contamination", "taxonomy"]:
            aggregation_exprs.append(pl.col(col).max().alias(col))
        else:
            aggregation_exprs.append(pl.col(col).first(ignore_nulls=True).alias(col))
    combined_data_lf = combined_data_lf.group_by(["query_id", FASTA_COLUMN]).agg(
        aggregation_exprs
    )
    combined_data_lf = combined_data_lf.with_columns(
        assign_rank_expr(combined_data_lf.collect_schema().names())
    )
    combined_data = combined_data_lf.collect()

    special_columns = ["Completeness", "Contamination", "taxonomy"]
    special_columns = [col for col in special_columns if col in combined_data.columns]
    combined_data = organize_columns(combined_data, special_columns=special_columns)

    sort_columns = [
        col
        for col in [FASTA_COLUMN, "scaffold", "gene_number"]
        if col in combined_data.columns
    ]
    if sort_columns:
        combined_data = combined_data.sort(sort_columns)

    combined_data.write_csv(output, separator="\t")
    logger.info(f"Combined annotations saved to {output}, with corrected gene numbers.")


if __name__ == "__main__":
    combine_annotations()
