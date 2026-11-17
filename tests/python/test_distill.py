"""bin/distill.py (SUMMARIZE): Gene Counts in summarized_genomes.tsv."""

import csv
import subprocess
import sys

from conftest import BIN

TRNA_COLUMNS = (
    "input_fasta\tquery_id\ttRNA #\tbegin\tend\ttype\tcodon\tscore\tnote\tgene_id\n"
)


def test_trnas_count_once_each_even_when_they_share_a_scaffold(tmp_path):
    (tmp_path / "annots.tsv").write_text(
        "query_id\tinput_fasta\tkofam_id\ng1_s1_1\tg1\tK00001\n"
    )
    # tRNAs are keyed by scaffold: two Gly (GCC) and one Ala (CGC) on scaffold s1
    (tmp_path / "trnas.tsv").write_text(
        TRNA_COLUMNS
        + "g1\tg1_s1\t1\t1\t75\tGly\tGCC\t79.2\t\tGly (GCC)\n"
        + "g1\tg1_s1\t2\t90\t165\tGly\tGCC\t79.2\t\tGly (GCC)\n"
        + "g1\tg1_s1\t3\t200\t275\tAla\tCGC\t70.0\t\tAla (CGC)\n"
    )
    subprocess.run(
        [
            sys.executable,
            BIN / "distill.py",
            "-i",
            "annots.tsv",
            "--trna_path",
            "trnas.tsv",
        ],
        cwd=tmp_path,
        check=True,
    )
    with open(tmp_path / "summarized_genomes.tsv") as handle:
        counts = {r["gene_id"]: r["g1"] for r in csv.DictReader(handle, delimiter="\t")}
    assert (counts["`Gly (GCC)`"], counts["`Ala (CGC)`"]) == ("2", "1")
