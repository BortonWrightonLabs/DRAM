"""The scripts behind ADD_ANNOTATIONS, ADD_BIN_QUALITY, ADD_TAXA and MERGE_ANNOTATIONS."""

import csv
import subprocess
import sys

from conftest import BIN

GENES = "query_id\tinput_fasta\tstart_position\tstop_position\tstrandedness\tkofam_id\n"
GENES += "g1_s_1\tg1\t1\t90\t1\tK00001\ng2_s_1\tg2\t5\t95\t-1\t\n"


def run(script, *args):
    subprocess.run([sys.executable, BIN / script, "input_fasta", *args], check=True)


def read(path):
    with open(path) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return reader.fieldnames, {r["query_id"]: r for r in reader}


def test_add_bin_quality(tmp_path):
    (tmp_path / "annots.tsv").write_text(GENES)
    (tmp_path / "checkm.tsv").write_text(
        "Name\tCompleteness\tContamination\tx\ng1\t90.5\t1.2\t0\n"
    )
    run(
        "add_bin_quality.py",
        tmp_path / "annots.tsv",
        tmp_path / "checkm.tsv",
        tmp_path / "out.tsv",
    )
    columns, rows = read(tmp_path / "out.tsv")
    assert columns[-3:] == [
        "Completeness",
        "Contamination",
        "kofam_id",
    ]  # genome metadata before databases
    assert (rows["g1_s_1"]["Completeness"], rows["g2_s_1"]["Completeness"]) == (
        "90.5",
        "",
    )


def test_add_taxa(tmp_path):
    (tmp_path / "annots.tsv").write_text(GENES)
    (tmp_path / "gtdb.tsv").write_text(
        "user_genome\tclassification\nB\tx\ng2\td__Archaea\n"
    )
    run(
        "add_taxa.py",
        tmp_path / "annots.tsv",
        tmp_path / "gtdb.tsv",
        tmp_path / "out.tsv",
    )
    columns, rows = read(tmp_path / "out.tsv")
    assert columns[-2:] == ["taxonomy", "kofam_id"]
    assert rows["g2_s_1"]["taxonomy"] == "d__Archaea"


def test_add_annotations_puts_user_columns_last(tmp_path):
    (tmp_path / "old.tsv").write_text(GENES)
    (tmp_path / "new.tsv").write_text(
        "query_id\tinput_fasta\tstart_position\tstop_position\tstrandedness\tmy_note\n"
        "g1_s_1\tg1\t1\t90\t1\tchecked\n"
    )
    run(
        "add_annotations.py",
        tmp_path / "old.tsv",
        tmp_path / "new.tsv",
        tmp_path / "out.tsv",
    )
    columns, rows = read(tmp_path / "out.tsv")
    assert columns[-2:] == ["kofam_id", "my_note"]
    assert rows["g1_s_1"]["my_note"] == "checked"


def test_merge_annotations_ranks_and_orders(tmp_path):
    annotations = tmp_path / "annotations"
    annotations.mkdir()
    (annotations / "a.tsv").write_text(
        "query_id\tinput_fasta\tstart_position\tstop_position\tstrandedness\tkegg_bitScore\tkegg_id\n"
        "g1_s_1\tg1\t1\t90\t1\t400\tK00001\n"
    )
    (annotations / "b.tsv").write_text(
        "query_id\tinput_fasta\tstart_position\tstop_position\tstrandedness\tuniref_bitScore\n"
        "g2_s_1\tg2\t5\t95\t-1\t70\n"
    )
    run("merge_annotations.py", annotations, tmp_path / "out.tsv")
    columns, rows = read(tmp_path / "out.tsv")
    assert (
        columns.index("rank")
        < columns.index("kegg_id")
        < columns.index("kegg_bitScore")
    )
    assert {g: r["rank"] for g, r in rows.items()} == {"g1_s_1": "A", "g2_s_1": "C"}
