import csv
import subprocess
import sys

from conftest import BIN, GENOMES, OWC, called_genes


def test_gff_coordinates_match_dram1():
    dram1 = {
        r["query_id"]: (
            f"{r['input_fasta']}_{r['scaffold']}",
            r["start_position"],
            r["end_position"],
            "+" if r["strandedness"] == "1" else "-",
        )
        for r in csv.DictReader(
            open(OWC / "annotation/dram1_informed_annotations.tsv"), delimiter="\t"
        )
    }
    gff = {}
    for genome in GENOMES:
        out = subprocess.run(
            [sys.executable, BIN / "generate_gff.py", called_genes(genome)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        assert out[0] == "##gff-version 3"
        # GFF ID is Prodigal's own (ID=1_1), so pair rows with FASTA headers by order
        genes = [
            line[1:].split(" ", 1)[0]
            for line in called_genes(genome).read_text().splitlines()
            if line.startswith(">")
        ]
        assert len(genes) == len(out) - 1
        for gene, line in zip(genes, out[1:]):
            seqid, source, kind, start, end, _, strand, phase, _ = line.split("\t")
            assert (source, kind, phase) == ("Prodigal", "CDS", "0")
            gff[gene] = (seqid, start, end, strand)
    assert gff.keys() == dram1.keys()
    assert gff == dram1
