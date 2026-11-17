from pathlib import Path
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

    def test_keeps_every_column_once(self):
        columns = ["kegg_id", "query_id", "rank", "rgi_aro", "x"]
        self.assertCountEqual(order_columns(columns), columns)


if __name__ == "__main__":
    unittest.main()
