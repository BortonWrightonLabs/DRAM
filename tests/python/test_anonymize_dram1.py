import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "anonymize_dram1", ROOT / "tests/scripts/anonymize_dram1.py"
)
anonymize_dram1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anonymize_dram1)

DRAM1_HEADER = [
    "",
    "fasta",
    "scaffold",
    "gene_position",
    "start_position",
    "end_position",
    "strandedness",
    "rank",
    "kegg_genes_id",
    "ko_id",
    "kegg_hit",
    "kegg_RBH",
    "kegg_identity",
    "kegg_bitScore",
    "kegg_eVal",
    "peptidase_id",
    "peptidase_family",
    "peptidase_hit",
    "peptidase_RBH",
    "peptidase_identity",
    "peptidase_bitScore",
    "peptidase_eVal",
    "pfam_hits",
    "cazy_ids",
    "cazy_hits",
    "cazy_subfam_ec",
    "cazy_best_hit",
    "heme_regulatory_motif_count",
]


def dram1_row(genome, scaffold, gene, ko="", family="", cazy="", **extra):
    row = dict.fromkeys(DRAM1_HEADER, "")
    row.update(
        {
            "": f"{genome}_{scaffold}_{gene}",
            "fasta": genome,
            "scaffold": scaffold,
            "gene_position": str(gene),
            "start_position": "10",
            "end_position": "90",
            "strandedness": "-1",
            "rank": "C",
            "ko_id": ko,
            "peptidase_family": family,
            "cazy_ids": cazy,
            "heme_regulatory_motif_count": "0",
        }
    )
    row.update(extra)
    return row


def run(rows, keep=("keepA", "keepB")):
    """Write a tiny DRAM1 annotate run, anonymize it; return (annotations, comparable IDs)."""
    with tempfile.TemporaryDirectory() as folder:
        annotate, out = Path(folder) / "annotate", Path(folder) / "out"
        annotate.mkdir()
        with open(annotate / "annotations.tsv", "w", newline="") as handle:
            writer = csv.DictWriter(handle, DRAM1_HEADER, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        args = ["--annotate", str(annotate), "--out", str(out)]
        for genome in keep:
            args += ["--keep", genome]
        anonymize_dram1.main(args)
        tables = []
        for name in ["annotations.tsv", "comparable_ids.tsv"]:
            with open(out / name) as handle:
                tables.append(list(csv.DictReader(handle, delimiter="\t")))
        return tables


class ConversionTests(unittest.TestCase):
    def test_dram1_row_becomes_an_anonymous_dram2_row(self):
        row = dram1_row(
            "keepA",
            "k121_77",
            3,
            ko="K00950",
            kegg_genes_id="aba:Acid345_2209",
            kegg_hit="aba:Acid345_2209 (K01737) queD; synthase [EC:4.2.3.12 4.1.2.50 2.4.-.-]",
            kegg_bitScore="178.0",
            peptidase_id="MER0025057",
            family="M23B",
            peptidase_hit="MER0025057 - yomI g.p.",
            peptidase_bitScore="72.0",
            pfam_hits="FAD binding domain [PF01565.26]; DUF3683 [PF12447.11]",
            cazy="GH13; GH13_26",
            cazy_hits="GH13 alpha-amylase (EC 3.2.1.1);",
            cazy_subfam_ec="3.2.1.1,3.2.1.133; 5.4.99.15",
            cazy_best_hit="GH13.hmm",
        )

        [out] = run([row, dram1_row("keepB", "k121_5", 1)])[0][:1]

        self.assertEqual(
            out,
            {
                "query_id": "genome_01_scaffold_0001_3",
                "input_fasta": "genome_01",
                "scaffold": "genome_01_scaffold_0001",
                "gene_number": "3",
                "start_position": "10",
                "stop_position": "90",
                "strandedness": "-1",
                "rank": "C",
                "kofam_id": "K00950",
                "kofam_EC": "EC:4.2.3.12; EC:4.1.2.50",  # complete ECs only, as DRAM2 writes them
                "kofam_full_bitScore": "178.0",
                "merops_id": "MER0025057",
                "merops_family": "M23B",
                "merops_description": "MER0025057 - yomI g.p.",
                "merops_bitScore": "72.0",
                "pfam_id": "PF01565.26; PF12447.11",
                "pfam_description": "FAD binding domain [PF01565.26]; DUF3683 [PF12447.11]",
                # DRAM2's dbCAN HMM search writes families and subfamilies to
                # dbcan_id; dbcan_sub_id is dbCAN-sub, which DRAM1 never ran
                "dbcan_id": "GH13;GH13_26",
                "dbcan_description": "GH13 alpha-amylase (EC 3.2.1.1);",
                "dbcan_sub_ec": "3.2.1.1;3.2.1.133;5.4.99.15",
                "heme_regulatory_motif_count": "0",
            },
        )

    def test_scaffolds_are_numbered_per_genome_and_reused(self):
        rows = [
            dram1_row("keepA", "k121_9", 1),
            dram1_row("keepA", "k121_9", 2),
            dram1_row("keepA", "k121_4", 1),
            dram1_row("keepB", "k121_9", 1),
        ]

        ids = [r["query_id"] for r in run(rows)[0]]

        self.assertEqual(
            ids,
            [
                "genome_01_scaffold_0001_1",
                "genome_01_scaffold_0001_2",
                "genome_01_scaffold_0002_1",
                "genome_02_scaffold_0001_1",
            ],
        )


class SelectionTests(unittest.TestCase):
    def test_other_genomes_keep_only_rows_with_ids_the_kept_genomes_lack(self):
        rows = [
            dram1_row("keepA", "s1", 1, ko="K1"),
            dram1_row("keepB", "s1", 1, family="M1"),
            dram1_row("other", "s1", 1, ko="K1"),  # KO already covered: dropped
            dram1_row("other", "s1", 2, ko="K2"),  # rare KO: kept
            dram1_row("other", "s1", 3, ko="K2"),  # every row with a rare ID: kept
            dram1_row("other", "s2", 1, family="M2"),  # rare MEROPS family: kept
            dram1_row("other", "s2", 2, cazy="GH5; GH5_2"),  # rare CAZy: kept
            dram1_row("other", "s2", 3),  # no IDs at all: dropped
        ]

        out, _ = run(rows)

        self.assertEqual(
            [
                (r["input_fasta"], r["kofam_id"], r["merops_family"], r["dbcan_id"])
                for r in out
            ],
            [
                ("genome_01", "K1", "", ""),
                ("genome_02", "", "M1", ""),
                ("genome_03", "K2", "", ""),
                ("genome_03", "K2", "", ""),
                ("genome_03", "", "M2", ""),
                ("genome_03", "", "", "GH5;GH5_2"),
            ],
        )

    def test_lists_the_ids_whose_counts_still_match_dram1(self):
        # A kept row also carries IDs genome_01/02 already have; those IDs' other
        # rows were dropped, so only the IDs 01/02 lack keep their DRAM1 counts.
        rows = [
            dram1_row("keepA", "s1", 1, ko="K1"),
            dram1_row("keepB", "s1", 1),
            dram1_row("other", "s1", 1, ko="K1"),  # K1 covered: dropped
            dram1_row(
                "other", "s1", 2, ko="K1", family="M2"
            ),  # kept for M2, carries K1
            dram1_row("other", "s1", 3, cazy="GH5; GH5_2"),
        ]

        _, comparable = run(rows)

        self.assertEqual(
            comparable,
            [
                {"input_fasta": "genome_03", "id_type": "cazy", "id": "GH5"},
                {"input_fasta": "genome_03", "id_type": "cazy", "id": "GH5_2"},
                {"input_fasta": "genome_03", "id_type": "merops", "id": "M2"},
            ],
        )
