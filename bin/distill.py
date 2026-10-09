#!/usr/bin/env python
"""This is the script that distills the genomes"""

import click
import os
from pathlib import Path
import polars as pl
from utils.logger import get_logger
from utils.click_utils import validate_comma_separated
from utils.excel import write_summarized_genomes_to_xlsx
from utils.pl_utils import read_csv
from rule_parser.src.rules import evaluate_rules_on_anno, ID_EXPR_DICT

logger = get_logger(filename=Path(__file__).stem)

(
    COL_GENE_ID,
    COL_GENE_DESCRIPTION,
    COL_PATHWAY,
    COL_MODULE,
    COL_SHEET,
    COL_HEADER,
    COL_SUBHEADER,
    COL_ALIAS,
    COL_RULE,
) = (
    "gene_id",
    "gene_description",
    "pathway",
    "module",
    "topic_ecosystem",
    "header",
    "subheader",
    "alias",
    "rule",
)
OPTIONAL_COLUMNS = [COL_ALIAS, COL_RULE]
RRNA_COLUMNS = [COL_GENE_ID, COL_GENE_DESCRIPTION, COL_SHEET, COL_HEADER, COL_SUBHEADER]
TRNA_COLUMNS = RRNA_COLUMNS + ["AA_type"]
CORE_COLUMNS = RRNA_COLUMNS + [COL_MODULE]
FRAME_COLUMNS = CORE_COLUMNS + OPTIONAL_COLUMNS
RRNA_TYPES = ["5S rRNA", "16S rRNA", "23S rRNA"]
TAXONOMY_LEVELS = ["d", "p", "c", "o", "f", "g", "s"]
CONSTANT_DISTILLATE_COLUMNS = [
    COL_GENE_ID,
    COL_GENE_DESCRIPTION,
    COL_MODULE,
    COL_HEADER,
    COL_SUBHEADER,
]
DISTILATE_SORT_ORDER_COLUMNS = [COL_HEADER, COL_SUBHEADER, COL_MODULE, COL_GENE_ID]
EXCEL_MAX_CELL_SIZE = 32767

FASTA_COLUMN = os.getenv("FASTA_COLUMN", "input_fasta")
DISTILL_DIR = Path(__file__).parent / "assets/forms/distill_sheets"
DEFAULT_GROUPBY_COLUMN = COL_SHEET
# Genes are keyed on genome + query_id; \x1f (unit separator) cannot occur in either.
GENE_KEY = "_gene_key"
GENE_KEY_SEPARATOR = "\x1f"


def check_columns(data, logger):
    functions = [i for i in ID_EXPR_DICT if i in data.columns]
    missing = [i for i in ID_EXPR_DICT if i not in data.columns]
    logger.info(
        "Note: the following id fields "
        f"were not in the annotations file and are not being used: {missing},"
        f" but these are {functions}"
    )


def make_genome_summary(
    annotations, genome_summary_frame: pl.LazyFrame, logger, fasta_column=FASTA_COLUMN
):
    if COL_RULE not in genome_summary_frame.collect_schema().names():
        genome_summary_frame = genome_summary_frame.with_columns(
            pl.lit(None).cast(pl.String).alias(COL_RULE)
        )

    genome_summary_frame = genome_summary_frame.with_columns(
        pl.when(pl.col(COL_RULE).is_not_null())
        .then(pl.col(COL_RULE))
        .otherwise(pl.col("gene_id"))
        .alias(COL_RULE)
    )
    # A gene is identified by its genome AND its query_id. query_id alone is not
    # unique across genomes: per-sample assemblers reuse contig names (MEGAHIT
    # k141_*), so the same "k141_100_1" occurs in many bins. Keying on query_id
    # alone merged unrelated genes in the rule evaluation and credited every hit
    # to every genome sharing the id.
    annotations = annotations.with_columns(
        pl.concat_str(
            [pl.col(fasta_column).cast(pl.String), pl.col("query_id").cast(pl.String)],
            separator=GENE_KEY_SEPARATOR,
        ).alias(GENE_KEY)
    )
    df = evaluate_rules_on_anno(
        rules=genome_summary_frame,
        # rules_tsv_path="/home/projects-wrighton-2/Pipeline_Development/DRAM2-Nextflow/DRAM/bin/assets/forms/distill_sheets/distill_metals.tsv",
        annotations=annotations,
        count_col=GENE_KEY,
        label_col="gene_id",
        alias_col=None,
        rules_col=COL_RULE,
    )
    df = df.join(
        annotations.select([pl.col(GENE_KEY), pl.col(fasta_column)]).unique(),
        on=GENE_KEY,
    ).drop(GENE_KEY)
    df = df.group_by(fasta_column).agg(pl.exclude(fasta_column).sum())

    df = df.select(pl.exclude(fasta_column)).transpose(
        include_header=True, header_name="gene_id", column_names=df[fasta_column]
    )

    df = genome_summary_frame.collect().join(df, on="gene_id", how="left")

    df = df.drop(OPTIONAL_COLUMNS, strict=False)

    return df


# TODO: add assembly stats like N50, longest contig, total assembled length etc
def make_genome_stats(
    annotations: pl.DataFrame,
    rrna_frame: pl.DataFrame = None,
    trna_frame: pl.DataFrame = None,
    quast_frame: pl.DataFrame = None,
    fasta_column: str = FASTA_COLUMN,
):
    rows = list()
    columns = ["genome"]
    if "scaffold" in annotations.columns:
        columns.append("number of scaffolds")
    if "bin_taxonomy" in annotations.columns:
        columns.append("taxonomy")
    if "bin_completeness" in annotations.columns:
        columns.append("completeness score")
    if "bin_contamination" in annotations.columns:
        columns.append("contamination score")
    for genome, frame in annotations.group_by(fasta_column):
        row = [genome[0]]
        if "scaffold" in frame.columns:
            row.append(len(set(frame["scaffold"])))
        if "bin_taxonomy" in frame.columns:
            row.append(frame["bin_taxonomy"][0])
        if "bin_completeness" in frame.columns:
            row.append(frame["bin_completeness"][0])
        if "bin_contamination" in frame.columns:
            row.append(frame["bin_contamination"][0])
        rows.append(row)
    genome_stats = pl.DataFrame(rows, schema=columns, orient="row")
    if rrna_frame is not None:
        # Identify the "sample" columns (everything that's not metadata)
        meta_cols = RRNA_COLUMNS
        sample_cols = [c for c in rrna_frame.columns if c not in meta_cols]

        # group_by gene_id, sum sample columns
        df_rrna = rrna_frame.group_by("gene_id").agg(
            [pl.col(c).sum().alias(c) for c in sample_cols]
        )

        # transpose: rows -> genomes (samples), columns -> gene_id
        # This creates a "genome" column from original sample column names
        df_rrna = df_rrna.transpose(
            include_header=True,
            header_name="genome",  # new first column name
            column_names="gene_id",  # column headers come from gene_id values
        )

        genome_stats = genome_stats.join(df_rrna, on="genome", how="inner")
        assert genome_stats.shape[0] == df_rrna.shape[0], (
            "genomes from annotation file don't map to rrna file"
        )
    if trna_frame is not None:
        meta_cols = TRNA_COLUMNS

        sample_cols = [c for c in trna_frame.columns if c not in meta_cols]

        df_trna = (
            trna_frame.filter(~pl.col("AA_type").is_in(["Undet", "Sup"]))
            .group_by("AA_type")
            .agg([pl.col(c).sum().alias(c) for c in sample_cols])
            .select(
                [(pl.col(c) != 0).cast(pl.Int64).sum().alias(c) for c in sample_cols]
            )
            .transpose(
                include_header=True, header_name="genome", column_names=["tRNA count"]
            )
        )
        genome_stats = genome_stats.join(df_trna, on="genome", how="inner")

    if quast_frame is not None:
        quast_frame = quast_frame.rename({fasta_column: "genome"}).drop("no. contigs")

        genome_stats = genome_stats.join(quast_frame, on="genome", how="inner")
        assert genome_stats.shape[0] == quast_frame.shape[0], (
            "genomes from annotation file don't map to quast file"
        )

    return genome_stats


@click.command()
@click.option("-i", "--input_file", required=True, help="Annotations path")
# @click.option("-o", "--output_dir", required=True, help="Directory to write summarized genomes")
@click.option("--trna_path", help="tRNA scan raw output from annotation")
@click.option(
    "--fasta_column",
    help="Column from annotations to use as fasta names",
    default=FASTA_COLUMN,
)
@click.option(
    "--distill_topics", default="default", help="Default distillates topics to run."
)
@click.option(
    "--distill_ecosystem",
    default="eng_sys,ag,bgc,gut,aquatic",
    help="Default distillates ecosystems to run.",
)
@click.option(
    "--custom_distillate",
    default=[],
    callback=validate_comma_separated,
    help="Custom distillate forms to add your own modules, comma separated. ",
)
@click.option(
    "--group_column",
    "-g",
    type=str,
    help="Column in rules/summarize files to group by in in the Summarize sheets (creates separate excel sheets)",
    default=DEFAULT_GROUPBY_COLUMN,
)
def distill(
    input_file,
    trna_path=None,
    fasta_column=FASTA_COLUMN,
    distill_topics=None,
    distill_ecosystem=None,
    custom_distillate=None,
    group_column=None,
):
    """Summarize metabolic content of annotated genomes"""

    # read in data
    try:
        annotations = pl.read_csv(
            input_file, separator="\t", infer_schema_length=10_000
        )
    except Exception:
        annotations = pl.read_csv(input_file, separator="\t", infer_schema_length=None)
    if "bin_taxnomy" in annotations:
        annotations = annotations.sort_values("bin_taxonomy")

    # Check the columns are present
    check_columns(annotations, logger)

    trna_frame = read_csv(trna_path)

    distill_topic_sheets = []
    if ("assim" in distill_topics) or ("default" in distill_topics):
        distill_topic_sheets.append(
            DISTILL_DIR / "assimilation_and_cofactor_metabolism.tsv"
        )
    if ("cell" in distill_topics) or ("default" in distill_topics):
        distill_topic_sheets.append(DISTILL_DIR / "cellular_machinery.tsv")
    if ("energy" in distill_topics) or ("default" in distill_topics):
        distill_topic_sheets.append(
            DISTILL_DIR / "energy_acquisition_bioenergetics.tsv"
        )
    if ("env" in distill_topics) or ("default" in distill_topics):
        distill_topic_sheets.append(
            DISTILL_DIR / "environmental_interaction_and_adaptation.tsv"
        )

    distill_ecos_sheets = []
    if "ag" in distill_ecosystem:
        distill_ecos_sheets.append(DISTILL_DIR / "distill_ag.tsv")
    if "eng_sys" in distill_ecosystem:
        distill_ecos_sheets.append(DISTILL_DIR / "distill_eng_sys.tsv")
    if "bgc" in distill_ecosystem:
        distill_ecos_sheets.append(DISTILL_DIR / "distill_bgc.tsv")
    if "gut" in distill_ecosystem:
        distill_ecos_sheets.append(DISTILL_DIR / "distill_gut.tsv")
    if "aquatic" in distill_ecosystem:
        distill_ecos_sheets.append(DISTILL_DIR / "distill_aquatic.tsv")

    distill_custom_sheets = []
    if custom_distillate:
        for custom_sheet in custom_distillate:
            distill_custom_sheets.append(Path(custom_sheet))

    genome_summary_form = pl.concat(
        [
            *[
                pl.scan_csv(s, separator="\t")
                .select(
                    [
                        c
                        for c in FRAME_COLUMNS
                        if c in pl.scan_csv(s, separator="\t", n_rows=0).columns
                    ]
                )
                .with_columns(
                    workbook=pl.lit(s.stem + "_summary"),
                )
                for s in distill_topic_sheets
            ],
            *[
                pl.scan_csv(s, separator="\t")
                .select(
                    [
                        c
                        for c in FRAME_COLUMNS
                        if c in pl.scan_csv(s, separator="\t", n_rows=0).columns
                    ]
                )
                .with_columns(
                    workbook=pl.lit("ecosystem_summary"),
                )
                for s in distill_ecos_sheets
            ],
            *[
                pl.scan_csv(s, separator="\t")
                .select(
                    [
                        c
                        for c in FRAME_COLUMNS
                        if c in pl.scan_csv(s, separator="\t", n_rows=0).columns
                    ]
                )
                .with_columns(
                    workbook=pl.lit("custom_summary"),
                )
                for s in distill_custom_sheets
            ],
        ],
        how="diagonal",
    )

    logger.info("Retrieved distillate genome summary form")

    if trna_frame is not None:
        annotations = pl.concat(
            [
                annotations,
                trna_frame.select(
                    ["input_fasta", "query_id", pl.col("gene_id").alias("trna_id")]
                ),
            ],
            how="diagonal",
        )

    # make genome metabolism summary
    logger.info("Giving counts for genome metabolism summary")
    summarized_genomes = make_genome_summary(
        annotations, genome_summary_form, logger, fasta_column
    )
    summarized_genomes.write_csv("summarized_genomes.tsv", separator="\t")
    kw = {"extra_frames": []}
    for workbook_name, df in summarized_genomes.group_by("workbook"):
        workbook_name = workbook_name[0]
        write_summarized_genomes_to_xlsx(
            df=df,
            output_file=workbook_name + ".xlsx",
            group_by=group_column,
            sort_order_columns=DISTILATE_SORT_ORDER_COLUMNS,
            **kw,
        )
    logger.info("Generated genome metabolism summary")


if __name__ == "__main__":
    distill()
