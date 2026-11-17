"""Column order for annotation tables, shared by every step that writes them.

Metadata first (gene, then genome), then one group per database in alphabetical
order with `<db>_id` first, then any other columns (e.g. user-added annotations)
in their original order. Standard library only: steps run in pandas and polars
containers alike.
"""

import os

FASTA_COLUMN = os.getenv("FASTA_COLUMN", "input_fasta")
GENE_COLUMNS = [
    "query_id",
    FASTA_COLUMN,
    "scaffold",
    "gene_number",
    "start_position",
    "stop_position",
    "strandedness",
    "rank",
    "heme_regulatory_motif_count",
]
GENOME_COLUMNS = ["Completeness", "Contamination", "taxonomy"]


def database(column, databases):
    """The database a column belongs to: the longest prefix p with a `p_id` column.

    Every database search writes `<db>_id`, so multi-word names (cant_hyd, dram_db)
    need no list. Columns without one (e.g. RGI's rgi_aro) belong to no database.
    """
    return max(
        (db for db in databases if column.startswith(db + "_")), key=len, default=None
    )


def order_columns(columns):
    columns = list(columns)
    metadata = [c for c in GENE_COLUMNS + GENOME_COLUMNS if c in columns]
    rest = [c for c in columns if c not in metadata]
    databases = [c.removesuffix("_id") for c in rest if c.endswith("_id")]
    db = {c: database(c, databases) for c in rest}
    groups = sorted(set(db.values()) - {None})
    by_database = [
        c
        for group in groups
        for c in sorted(
            (c for c in rest if db[c] == group), key=lambda c: (c != f"{group}_id", c)
        )
    ]
    others = [c for c in rest if db[c] is None]
    return metadata + by_database + others
