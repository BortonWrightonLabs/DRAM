import csv
import subprocess

import pytest

from conftest import BIN, GENOMES, called_genes


@pytest.mark.parametrize("genome", GENOMES)
def test_gene_number_is_prodigal_gene_index(tmp_path, genome):
    table = tmp_path / "genes.tsv"
    subprocess.run(
        ["bash", BIN / "parse_faa.sh", called_genes(genome), table], check=True
    )
    rows = list(csv.DictReader(open(table), delimiter="\t"))
    assert rows
    # the gene number is the last _-separated part of the query ID (scaffold_gene)
    assert [r["gene_number"] for r in rows] == [
        r["query_id"].rsplit("_", 1)[1] for r in rows
    ]
