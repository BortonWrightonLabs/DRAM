import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

import pandas as pd


spec = importlib.util.spec_from_file_location(
    "mmseqs_add_descriptions",
    Path(__file__).resolve().parents[1] / "bin/mmseqs_add_descriptions.py",
)
descriptions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(descriptions)


class KeggDescriptionTests(unittest.TestCase):
    def test_header_and_legacy_orthologies(self):
        for header in (
            "aaa:Acav_0001 protein DnaA; K02313; dnaA",
            "aaa:Acav_0001 (K02313) dnaA; protein",
        ):
            with self.subTest(header=header):
                self.assertEqual(descriptions.extract_kegg_orthology(header), "K02313")

    def test_multiple_orthologies(self):
        self.assertEqual(
            descriptions.extract_kegg_orthology("gene (K00001/K00002); K00001"),
            "K00001/K00002",
        )

    def test_missing_or_invalid_orthologies(self):
        for header in (None, float("nan"), "", "protein K123456 AK00001 K00001x"):
            with self.subTest(header=header):
                self.assertIsNone(descriptions.extract_kegg_orthology(header))

    def test_ec_fields(self):
        self.assertEqual(
            descriptions.extract_kegg_EC(
                "enzyme [EC:1.18.1.7 2.3.4.5] [EC:1.18.1.7 3.4.21.-]"
            ),
            "EC:1.18.1.7; EC:2.3.4.5",
        )
        self.assertEqual(descriptions.extract_kegg_EC("protease [EC:3.4.21.-]"), "")
        for header in (None, "protein", "protein 1.2.3.4"):
            with self.subTest(header=header):
                self.assertIsNone(descriptions.extract_kegg_EC(header))

    def test_formatted_output_uses_metadata_then_header(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = root / "hits.tsv"
            loci = root / "loci.tsv"
            metadata = root / "metadata.tsv"
            output = root / "output.csv"
            raw.write_text(
                "query\ttarget\tbits\ttheader\n"
                "q1\tgene1\t120\tgene1 enzyme; K00001 [EC:1.2.3.4]\n"
                "q2\tgene2\t80\tgene2 enzyme; K00002 [EC:2.3.4.5]\n"
            )
            loci.write_text(
                "query_id\tstart_position\tstop_position\nq1\t1\t90\nq2\t91\t180\n"
            )
            metadata.write_text(
                "id\tdescription\tA_rank\tB_rank\n"
                "gene1\tcurated (K99999) enzyme [EC:9.8.7.6]\t100\t60\n"
            )
            for info, expected in (
                ("NULL", ["K00001", "K00002"]),
                (metadata, ["K99999", "K00002"]),
            ):
                with (
                    self.subTest(metadata=info),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    descriptions.main("sample", "kegg", info, 60, loci, raw, output)
                    result = pd.read_csv(output)
                    self.assertEqual(result["kegg_id"].tolist(), expected)
                    self.assertEqual(
                        result["kegg_gene_name"].tolist(), ["gene1", "gene2"]
                    )
                    self.assertEqual(result["kegg_bitScore"].tolist(), [120, 80])
                    self.assertEqual(result.loc[1, "kegg_EC"], "EC:2.3.4.5")
                    self.assertNotIn("theader", result)
                    if info != "NULL":
                        self.assertEqual(result.loc[0, "kegg_EC"], "EC:9.8.7.6")
                        self.assertEqual(result.loc[0, "kegg_rank"], "A")


if __name__ == "__main__":
    unittest.main()
