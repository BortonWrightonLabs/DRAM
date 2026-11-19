from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bin"))

from utils.columns import order_columns


class OrderColumnsTests(unittest.TestCase):
    def test_order(self):
        shuffled = [
            "user_note",
            "taxonomy",
            "kofam_EC",
            "dram_db_id",
            "heme_regulatory_motif_count",
            "cant_hyd_bitScore",
            "kofam_id",
            "dbcan_sub_id",
            "query_id",
            "Completeness",
            "cant_hyd_id",
            "dbcan_id",
            "strandedness",
            "camper_id",
            "input_fasta",
            "custom_score",
            "rgi_aro",
            "dbcan_sub_ec",
            "kegg_id",
        ]
        self.assertEqual(
            order_columns(shuffled),
            [
                # gene metadata, then genome metadata
                "query_id",
                "input_fasta",
                "strandedness",
                "heme_regulatory_motif_count",
                "Completeness",
                "taxonomy",
                # databases A-Z, <db>_id first; cant_hyd and dram_db are not "cant"/"dram"
                "camper_id",
                "cant_hyd_id",
                "cant_hyd_bitScore",
                "dbcan_id",
                # dbcan_sub_id makes dbcan_sub its own group, right after dbcan
                "dbcan_sub_id",
                "dbcan_sub_ec",
                "dram_db_id",
                "kegg_id",
                "kofam_id",
                "kofam_EC",
                # columns with no <db>_id (user-added annotations, RGI) last, in order
                "user_note",
                "custom_score",
                "rgi_aro",
            ],
        )

    def test_sample_columns_last(self):
        # Sample names can look like databases (kegg_x) or Gene IDs (_id)
        columns = [
            "sample:S2",
            "kegg_id",
            "sample:kegg_x",
            "query_id",
            "sample:a_id",
            "x",
        ]
        self.assertEqual(
            order_columns(columns),
            ["query_id", "kegg_id", "x", "sample:S2", "sample:kegg_x", "sample:a_id"],
        )

    def test_keeps_every_column_once(self):
        columns = ["kegg_id", "query_id", "rank", "rgi_aro", "x"]
        self.assertCountEqual(order_columns(columns), columns)


def test_standard_library_only():
    """columns.py imports dram_rules.definitions; both must load without pandas or polars."""
    # -S: no site-packages, so any import outside the standard library fails
    result = subprocess.run(
        [sys.executable, "-S", "-c", "import utils.columns"],
        cwd=Path(__file__).resolve().parents[2] / "bin",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "utils/columns.py and dram_rules.definitions must import only the "
        f"standard library:\n{result.stderr}"
    )


if __name__ == "__main__":
    unittest.main()
