"""hmm_parser.py on OWC against the mini databases.

Expected hits were recorded with the full databases/ (the HMM minis reproduce them
exactly, see tests/data/db/README.md). Bit scores and IDs only, never e-values.
"""

import csv

import pytest

from conftest import DB, search_hmm


def rows(paths, db_name):
    return sorted(
        (r["query_id"], r[f"{db_name}_id"], float(r[f"{db_name}_full_bitScore"]))
        for path in paths
        for r in csv.DictReader(open(path))
    )


def test_kofam_threshold_and_ec(kofam_hits):
    assert rows(kofam_hits, "kofam") == sorted(
        [
            ("OWC_0000_k121_3157_3", "K03388", 1131.2),
            ("OWC_0000_k121_3157_4", "K00441", 320.1),
            ("OWC_0000_k121_3157_5", "K08264", 316.6),
            ("OWC_0000_k121_3157_2", "K14127", 250.7),
            ("OWC_0001_k121_21365628_14", "K24689", 309.1),
            ("OWC_0001_k121_21365628_5", "K01990", 306.6),
            ("OWC_0001_k121_21365628_11", "K09711", 243.8),
            ("OWC_0001_k121_21365628_8", "K05770", 27.1),
        ]
    )
    ec = {
        r["query_id"]: r["kofam_EC"]
        for path in kofam_hits
        for r in csv.DictReader(open(path))
    }
    # partial ECs (1.12.99.-) are kept, as the ko_list definition gives them
    assert ec["OWC_0000_k121_3157_2"] == "EC:1.12.99.-; EC:1.8.98.5; EC:1.8.98.6"
    assert ec["OWC_0001_k121_21365628_8"] == ""


def test_vogdb_without_info_sheet(vogdb_hits):
    assert rows(vogdb_hits, "vogdb") == sorted(
        [
            ("OWC_0000_k121_43717_3", "VOG26141", 16.2),
            ("OWC_0000_k121_3157_5", "VOG07568", 15.2),
            ("OWC_0001_k121_21365628_5", "VOG19828", 74.3),
            ("OWC_0001_k121_21365628_9", "VOG09693", 28.4),
            ("OWC_0001_k121_21365628_2", "VOG00027", 20.6),
        ]
    )


@pytest.mark.parametrize(
    "db_name, folder, sheet",
    [
        ("camper", "camper_hmm", "camper_hmm_scores.tsv"),
        ("dram_db", "dram_db", "dram_db_scores.tsv"),
        ("cant_hyd", "canthyd_hmm", "cant_hyd_HMM_scores.tsv"),
    ],
)
def test_no_passing_hit_writes_nothing(tmp_path, db_name, folder, sheet):
    # OWC scores below these databases' thresholds (or has no hit), so the search
    # runs and the parser writes no file
    assert search_hmm(tmp_path, db_name, DB / folder, DB / folder / sheet) == []
    assert (tmp_path / "OWC_0000_hmmsearch.out").exists()
