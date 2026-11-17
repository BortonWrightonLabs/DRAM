import contextlib
import csv
import shutil
from pathlib import Path
import sys
import tempfile
import unittest

from click.testing import CliRunner
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bin"))

# Importing opens combine_annotations.log in the cwd (the pipeline publishes it),
# so import from a temp dir to keep the log out of the repo.
_log_dir = tempfile.TemporaryDirectory()
with contextlib.chdir(_log_dir.name):
    from combine_annotations import combine_annotations


class RgiAnnotationTests(unittest.TestCase):
    def test_rgi_annotations_join_called_genes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            genes = root / "genes"
            rgi = root / "rgi"
            genes.mkdir()
            rgi.mkdir()
            (genes / "sample_called_genes.faa").write_text(
                ">sample_scaffold_1 # 1 # 9 # 1\nMKK\n"
                ">sample_scaffold_2 # 10 # 18 # -1\nMAA\n"
            )
            with (rgi / "sample.txt").open("w") as handle:
                writer = csv.writer(handle, delimiter="\t")
                writer.writerow(
                    [
                        "ORF_ID",
                        "Contig",
                        "Best_Hit_Bitscore",
                        "Best_Hit_ARO",
                        "ARO",
                        "Drug Class",
                        "Resistance Mechanism",
                        "AMR Gene Family",
                    ]
                )
                writer.writerow(
                    [
                        "sample_scaffold_1_1 # 1 # 9 # 1",
                        "sample_scaffold_1",
                        "792.341",
                        "adeF",
                        "3000777",
                        "fluoroquinolone; tetracycline",
                        "antibiotic efflux",
                        "RND antibiotic efflux pump",
                    ]
                )
            output = root / "annotations.tsv"
            result = CliRunner().invoke(
                combine_annotations,
                [
                    "--genes_dir",
                    str(genes),
                    "--rgi_dir",
                    str(rgi),
                    "--output",
                    str(output),
                ],
            )
            self.assertEqual(result.exit_code, 0, result.output)
            frame = pl.read_csv(output, separator="\t", infer_schema=False)
            self.assertEqual(frame.height, 2)
            hit, missing = frame.to_dicts()
            self.assertEqual(hit["query_id"], "sample_scaffold_1")
            self.assertEqual(hit["input_fasta"], "sample")
            self.assertEqual(float(hit["rgi_best_hit_bitscore"]), 792.341)
            self.assertEqual(hit["rgi_aro"], "3000777")
            self.assertEqual(hit["rgi_best_hit_aro"], "adeF")
            self.assertEqual(hit["rgi_drug_class"], "fluoroquinolone; tetracycline")
            self.assertEqual(hit["rgi_resistance_mechanism"], "antibiotic efflux")
            self.assertEqual(hit["rgi_amr_gene_family"], "RND antibiotic efflux pump")
            self.assertIsNone(missing["rgi_aro"])
            self.assertIsNone(missing["rgi_best_hit_aro"])
            (rgi / "sample.txt").write_text(
                (rgi / "sample.txt").read_text().splitlines()[0] + "\n"
            )
            for rgi_path in [rgi, root / "disabled"]:
                with self.subTest(rgi_path=rgi_path):
                    result = CliRunner().invoke(
                        combine_annotations,
                        [
                            "--genes_dir",
                            str(genes),
                            "--rgi_dir",
                            str(rgi_path),
                            "--output",
                            str(output),
                        ],
                    )
                    self.assertEqual(result.exit_code, 0, result.output)
                    frame = pl.read_csv(output, separator="\t")
                    self.assertEqual(frame.height, 2)
                    if "rgi_aro" in frame.columns:
                        self.assertEqual(frame["rgi_aro"].null_count(), 2)


def test_owc_hits_join_called_genes(tmp_path, kofam_hits, vogdb_hits):
    from conftest import OWC
    from utils.columns import order_columns

    annotations = tmp_path / "annotations"
    annotations.mkdir()
    for hits in kofam_hits + vogdb_hits:
        shutil.copy(hits, annotations)
    output = tmp_path / "raw-annotations.tsv"
    result = CliRunner().invoke(
        combine_annotations,
        ["--annotations_dir", str(annotations)]
        + ["--genes_dir", str(OWC / "called_genes"), "--output", str(output)],
    )
    assert result.exit_code == 0, result.output
    with open(output) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        assert reader.fieldnames == order_columns(reader.fieldnames)
        combined = {r["query_id"]: r for r in reader}

    with open(OWC / "annotation/dram1_informed_annotations.tsv") as handle:
        dram1 = {r["query_id"]: r for r in csv.DictReader(handle, delimiter="\t")}
    assert combined.keys() == dram1.keys()  # every called gene, hit or not
    for gene, r in combined.items():
        assert (r["start_position"], r["stop_position"], r["strandedness"]) == (
            dram1[gene]["start_position"],
            dram1[gene]["end_position"],
            dram1[gene]["strandedness"],
        )

    for db, paths in [("kofam", kofam_hits), ("vogdb", vogdb_hits)]:
        expected = {
            r["query_id"]: r[f"{db}_id"]
            for path in paths
            for r in csv.DictReader(open(path))
        }
        assert {g: r[f"{db}_id"] for g, r in combined.items() if r[f"{db}_id"]} == (
            expected
        )


if __name__ == "__main__":
    unittest.main()
