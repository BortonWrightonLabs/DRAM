"""A batch MMseqs search split by qsetid gives each genome the hits its own search gives."""

import subprocess

from conftest import BIN, DB, GENOMES, called_genes

COLUMNS = "query,target,fident,alnlen,mismatch,gapopen,qstart,qend,tstart,tend,evalue,bits,theader"
TARGET = DB / "uniref" / "uniref.mmsdb"


def run(*args):
    subprocess.run(["mmseqs", *map(str, args)], check=True, capture_output=True)


def best_hits(out, query_fastas, name, columns):
    """The MMSEQS_SEARCH steps: search, bits >= 60, best hit, convertalis."""
    query = out / f"{name}_query"
    run("createdb", *query_fastas, query)
    run(
        "search",
        query,
        TARGET,
        out / f"{name}_hits",
        out / f"{name}_tmp",
        "--threads",
        2,
    )
    run(
        "filterdb",
        "--filter-column",
        2,
        "--comparison-operator",
        "ge",
        "--comparison-value",
        60,
        out / f"{name}_hits",
        out / f"{name}_passing",
    )
    run("filterdb", out / f"{name}_passing", out / f"{name}_best", "--extract-lines", 1)
    tsv = out / f"{name}.tsv"
    run(
        "convertalis",
        query,
        TARGET,
        out / f"{name}_best",
        tsv,
        "--format-mode",
        4,
        "--format-output",
        columns,
    )
    return tsv


def lines(path):
    header, *rows = path.read_text().splitlines()
    return header, sorted(rows)


def test_batch_split_matches_per_genome_search(tmp_path):
    batch = best_hits(
        tmp_path, [called_genes(g) for g in GENOMES], "batch", "qsetid," + COLUMNS
    )
    samples = tmp_path / "samples.txt"
    # a sample with no hits still gets the header, as its own search would write
    samples.write_text("\n".join(GENOMES + ["nohit"]) + "\n")
    split = tmp_path / "split"
    split.mkdir()
    subprocess.run(
        [
            "bash",
            BIN / "split_mmseqs_batch.sh",
            batch,
            samples,
            split,
            "___mmseqs_uniref.tsv",
        ],
        check=True,
    )

    for genome in GENOMES:
        alone = best_hits(tmp_path, [called_genes(genome)], genome, COLUMNS)
        assert lines(split / f"{genome}___mmseqs_uniref.tsv") == lines(alone)
        assert lines(alone)[1], "fixture should have hits"
    assert lines(split / "nohit___mmseqs_uniref.tsv") == (
        COLUMNS.replace(",", "\t"),
        [],
    )
