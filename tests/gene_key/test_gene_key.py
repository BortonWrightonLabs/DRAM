"""Run with python3 -m unittest discover -s tests/gene_key -v (needs polars, scikit-bio,
click, lark, networkx and xlsxwriter, as in the annotate and distill module environments).

query_id is not unique across genomes: per-sample assemblers reuse contig names
(MEGAHIT k141_*), so two bins in one run can both contain a gene "k141_100_1".
These tests give two genomes a colliding gene id with different hits and check
that each genome keeps only its own hits, and that a genome's output does not
change when the other genome is added to or removed from the run.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BIN = ROOT / "bin"
FASTA_COLUMN = "input_fasta"
SHARED_ID = "k141_100_1"

# Per genome: called genes, KEGG hit per gene, dbCAN family per gene.
GENOMES = {
    "binA": {
        "genes": {SHARED_ID: (1, 300, 1)},
        "kegg": {SHARED_ID: "K01206"},
        "dbcan": {SHARED_ID: "GH29"},
    },
    "binB": {
        "genes": {SHARED_ID: (1, 450, -1), "k141_200_1": (5, 200, 1)},
        "kegg": {SHARED_ID: "K01186"},
        "dbcan": {SHARED_ID: "GH33"},
    },
}


def write_inputs(folder: Path, genomes: list[str]) -> dict:
    dirs = {name: folder / name for name in ["annotations", "genes", "dbcan"]}
    for path in dirs.values():
        path.mkdir(parents=True)
    for genome in genomes:
        data = GENOMES[genome]
        (dirs["genes"] / f"{genome}_called_genes.faa").write_text(
            "".join(
                f">{gene} # {start} # {stop} # {strand} # ID=1\nMCAACHKL\n"
                for gene, (start, stop, strand) in data["genes"].items()
            )
        )
        (dirs["annotations"] / f"{genome}___kegg_annotations.tsv").write_text(
            "query_id,kegg_id,kegg_bitScore\n"
            + "".join(f"{gene},{ko},400\n" for gene, ko in data["kegg"].items())
        )
        (dirs["dbcan"] / f"{genome}_dbCAN_hmm_results.tsv").write_text(
            "HMM Name\tTarget Name\ti-Evalue\n"
            + "".join(
                f"{family}.hmm\t{gene}\t1e-50\n" for gene, family in data["dbcan"].items()
            )
        )
        (dirs["dbcan"] / f"{genome}_dbCANsub_hmm_results.tsv").write_text(
            "Subfam Name\tSubfam Composition\tSubfam EC\tSubstrate\tTarget Name\ti-Evalue\n"
            + "".join(
                f"{family}_e1\t{family}_e1:1\t-\t-\t{gene}\t1e-50\n"
                for gene, family in data["dbcan"].items()
            )
        )
    return dirs


def combine(folder: Path, genomes: list[str]) -> pl.DataFrame:
    dirs = write_inputs(folder, genomes)
    output = folder / "raw_annotations.tsv"
    subprocess.run(
        [
            sys.executable,
            str(BIN / "combine_annotations.py"),
            "--annotations_dir", str(dirs["annotations"]),
            "--genes_dir", str(dirs["genes"]),
            "--dbcan_dir", str(dirs["dbcan"]),
            "--output", str(output),
        ],
        check=True,
        cwd=folder,
        env={**os.environ, "FASTA_COLUMN": FASTA_COLUMN},
    )
    return pl.read_csv(output, separator="\t")


def gene(frame: pl.DataFrame, genome: str, query_id: str) -> dict:
    rows = frame.filter(
        (pl.col(FASTA_COLUMN) == genome) & (pl.col("query_id") == query_id)
    )
    assert rows.height == 1, f"{genome}/{query_id}: {rows.height} rows"
    return rows.row(0, named=True)


class CombineAnnotationsGeneKeyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dram-gene-key-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_colliding_ids_keep_their_own_hits(self):
        raw = combine(self.folder / "both", ["binA", "binB"])
        self.assertEqual(raw.height, 3)
        a, b = gene(raw, "binA", SHARED_ID), gene(raw, "binB", SHARED_ID)
        self.assertEqual((a["kegg_id"], a["dbcan_id"]), ("K01206", "GH29"))
        self.assertEqual((b["kegg_id"], b["dbcan_id"]), ("K01186", "GH33"))
        self.assertEqual(a["dbcan_sub_id"], "GH29_e1")
        self.assertEqual((a["stop_position"], a["strandedness"]), (300, 1))
        self.assertEqual((b["stop_position"], b["strandedness"]), (450, -1))

    def test_genome_rows_do_not_depend_on_other_genomes(self):
        alone = combine(self.folder / "alone", ["binA"])
        both = combine(self.folder / "both", ["binA", "binB"])
        both_a = both.filter(pl.col(FASTA_COLUMN) == "binA").select(alone.columns)
        self.assertTrue(alone.equals(both_a), f"\n{alone}\n{both_a}")


class GenomeSummaryGeneKeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(BIN))
        os.environ.setdefault("FASTA_COLUMN", FASTA_COLUMN)
        # distill opens its log file in the working directory on import.
        temp = tempfile.TemporaryDirectory(prefix="dram-gene-key-")
        cls.addClassCleanup(temp.cleanup)
        cwd = os.getcwd()
        os.chdir(temp.name)
        try:
            import distill
        finally:
            os.chdir(cwd)

        cls.distill = distill

    def summarize(self, genomes: list[str]) -> pl.DataFrame:
        annotations = pl.DataFrame(
            [
                {"query_id": q, FASTA_COLUMN: g, "kegg_id": ko}
                for g in genomes
                for q, ko in GENOMES[g]["kegg"].items()
            ]
        )
        form = pl.LazyFrame(
            {
                "gene_id": ["K01206", "K01186"],
                "gene_description": ["fucosidase", "sialidase"],
                "module": ["HMO", "HMO"],
                "topic_ecosystem": ["test", "test"],
                "header": ["h", "h"],
                "subheader": ["s", "s"],
            }
        )
        return self.distill.make_genome_summary(
            annotations, form, self.distill.logger, FASTA_COLUMN
        )

    def counts(self, summary: pl.DataFrame, genome: str) -> dict:
        return dict(summary.select("gene_id", genome).iter_rows())

    def test_colliding_ids_are_counted_once_per_genome(self):
        summary = self.summarize(["binA", "binB"])
        self.assertEqual(self.counts(summary, "binA"), {"K01206": 1, "K01186": 0})
        self.assertEqual(self.counts(summary, "binB"), {"K01206": 0, "K01186": 1})

    def test_genome_counts_do_not_depend_on_other_genomes(self):
        alone = self.summarize(["binA"])
        both = self.summarize(["binA", "binB"])
        self.assertEqual(self.counts(alone, "binA"), self.counts(both, "binA"))


if __name__ == "__main__":
    unittest.main()
