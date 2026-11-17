"""Shared fixtures: OWC genes searched against the mini databases, as HMM_SEARCH does."""

from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "bin"
OWC = ROOT / "tests/data/owc"
DB = ROOT / "tests/data/db"
GENOMES = ["OWC_0000", "OWC_0001"]
DUMMY_SHEET = BIN / "assets/forms/distill_sheets/dummy.tsv"


def called_genes(genome):
    return OWC / "called_genes" / f"{genome}_called_genes.faa"


def search_hmm(out, db_name, hmm_dir, info, ec_from_info=False):
    """hmm_search.py + hmm_parser.py per genome; returns the formatted hits written."""
    out.mkdir(parents=True, exist_ok=True)
    hits = []
    for genome in GENOMES:
        locs = out / f"{genome}_locs.tsv"
        domtbl = out / f"{genome}_hmmsearch.out"
        csv = out / f"{genome}___formatted_{db_name}_hits.csv"
        subprocess.run(
            ["bash", BIN / "parse_faa.sh", called_genes(genome), locs], check=True
        )
        subprocess.run(
            [sys.executable, BIN / "hmm_search.py", "--hmm", hmm_dir]
            + ["--input_file", called_genes(genome), "--e_value", "1e-5"]
            + ["--output_file", domtbl, "--cpus", "2"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [sys.executable, BIN / "hmm_parser.py", "--hmm_domtbl", domtbl]
            + ["--hmm_info_path", info, "--gene_locs", locs, "--db_name", db_name]
            + ["--output", csv]
            + (["--ec_from_info"] if ec_from_info else []),
            check=True,
            capture_output=True,
        )
        if csv.exists():
            hits.append(csv)
    return hits


@pytest.fixture(scope="session")
def kofam_hits(tmp_path_factory):
    kofam = DB / "kofam"
    if not (kofam / "kofam.hmm").exists():
        pytest.fail(
            "KOfam mini database missing; build it as tests/data/db/README.md describes"
        )
    return search_hmm(
        tmp_path_factory.mktemp("kofam"),
        "kofam",
        kofam,
        kofam / "kofam_ko_list.tsv",
        ec_from_info=True,
    )


@pytest.fixture(scope="session")
def vogdb_hits(tmp_path_factory):
    return search_hmm(
        tmp_path_factory.mktemp("vogdb"), "vogdb", DB / "vogdb", DUMMY_SHEET
    )
