#!/usr/bin/env python3
"""Turn a DRAM1 run into anonymized DRAM2-format test fixtures (tests/data/dram1/).

The two `--keep` genomes become genome_01 and genome_02 with every row. The other
genomes (genome_03, ...) keep only the rows carrying a KO, MEROPS family or CAZy ID
that genome_01/02 lack, so the fixture still covers every ID of the run while staying
small. Every row carrying such an ID is kept, so its DRAM1 Gene Count still matches.
Genome, scaffold and gene names are rewritten; KEGG free text is dropped.
"""

import argparse
import csv
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

DRAM2_COLUMNS = [
    "query_id",
    "input_fasta",
    "scaffold",
    "gene_number",
    "start_position",
    "stop_position",
    "strandedness",
    "rank",
    "kofam_id",
    "kofam_EC",
    "kofam_full_bitScore",
    "merops_id",
    "merops_family",
    "merops_description",
    "merops_bitScore",
    "pfam_id",
    "pfam_description",
    "dbcan_id",
    "dbcan_description",
    "dbcan_sub_ec",
    "heme_regulatory_motif_count",
]
TRNA_COLUMNS = [
    "input_fasta",
    "query_id",
    "tRNA #",
    "begin",
    "end",
    "type",
    "codon",
    "score",
    "note",
    "gene_id",
]
SCAFFOLD = re.compile(r"k\d+_\d+")  # MEGAHIT contig names, as in <genome>_k121_77


def split(value, separators):
    return [part.strip() for part in re.split(separators, value or "") if part.strip()]


def row_ids(row):
    """The KO, MEROPS family and CAZy IDs a DRAM1 row carries."""
    return (
        {("ko", x) for x in split(row["ko_id"], ",")}
        | {("merops", x) for x in split(row["peptidase_family"], ";")}
        | {("cazy", x) for x in split(row["cazy_ids"], ";")}
    )


class Names:
    """Consistent new names: genome_NN, genome_NN_scaffold_NNNN."""

    def __init__(self, genomes):
        self.genomes = {old: f"genome_{i:02d}" for i, old in enumerate(genomes, 1)}
        self.scaffolds = {}

    def scaffold(self, genome, scaffold):
        key = (genome, scaffold)
        if key not in self.scaffolds:
            n = sum(1 for g, _ in self.scaffolds if g == genome) + 1
            self.scaffolds[key] = f"{self.genomes[genome]}_scaffold_{n:04d}"
        return self.scaffolds[key]

    def text(self, value):
        """Rewrite every genome and genome_scaffold name inside free text."""
        for old in sorted(self.genomes, key=len, reverse=True):
            value = re.sub(
                re.escape(old) + r"_(" + SCAFFOLD.pattern + ")",
                lambda m, old=old: self.scaffold(old, m[1]),
                value,
            )
            value = value.replace(old, self.genomes[old])
        return value


def convert(row, names):
    """One DRAM1 annotation row in DRAM2 columns, renamed."""
    scaffold = names.scaffold(row["fasta"], row["scaffold"])
    pfam = row["pfam_hits"]
    return {
        "query_id": f"{scaffold}_{row['gene_position']}",
        "input_fasta": names.genomes[row["fasta"]],
        "scaffold": scaffold,
        "gene_number": row["gene_position"],
        "start_position": row["start_position"],
        "stop_position": row["end_position"],
        "strandedness": row["strandedness"],
        "rank": row["rank"],
        # DRAM1 ran KEGG here; its KOs stand in for KOfam, which most DRAM2 runs use
        "kofam_id": "/".join(split(row["ko_id"], ",")),
        # kegg_hit is KEGG text: keep only its complete EC numbers. Real kofam_EC also
        # lists partial ECs, but dram-rules reads only complete ones
        "kofam_EC": "; ".join(
            f"EC:{ec}"
            for ec in dict.fromkeys(
                number
                for field in re.findall(r"\[EC:([^\]]*)\]", row["kegg_hit"] or "")
                for number in re.findall(r"\b\d+\.\d+\.\d+\.\d+\b", field)
            )
        ),
        "kofam_full_bitScore": row["kegg_bitScore"],
        "merops_id": row["peptidase_id"],
        "merops_family": row["peptidase_family"],
        "merops_description": row["peptidase_hit"],
        "merops_bitScore": row["peptidase_bitScore"],
        "pfam_id": "; ".join(re.findall(r"PF\d{5}\.\d+", pfam or "")),
        "pfam_description": pfam,
        # DRAM2's dbCAN HMM search writes families and subfamilies (GH13_26) to
        # dbcan_id; dbcan_sub_id holds dbCAN-sub clusters, which DRAM1 never ran
        "dbcan_id": ";".join(split(row["cazy_ids"], ";")),
        "dbcan_description": row["cazy_hits"],
        "dbcan_sub_ec": ";".join(split(row["cazy_subfam_ec"], "[;,]")),
        "heme_regulatory_motif_count": row["heme_regulatory_motif_count"],
    }


def read_tsv(path):
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return reader.fieldnames, list(reader)


def write_tsv(path, columns, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def anonymize_annotations(annotate, out, keep):
    """Write out/annotations.tsv; return the Names used."""
    _, rows = read_tsv(annotate / "annotations.tsv")
    others = sorted({row["fasta"] for row in rows} - set(keep))
    names = Names([*keep, *others])
    covered = set().union(*(row_ids(row) for row in rows if row["fasta"] in keep))
    kept = [row for row in rows if row["fasta"] in keep or row_ids(row) - covered]
    all_ids = set().union(*(row_ids(row) for row in rows))
    kept_ids = set().union(*(row_ids(row) for row in kept))
    assert kept_ids == all_ids, f"fixture lost {len(all_ids - kept_ids)} IDs"
    order = {genome: i for i, genome in enumerate(names.genomes)}
    kept.sort(
        key=lambda row: order[row["fasta"]]
    )  # stable: DRAM1 order within a genome
    # Only IDs genome_01/02 lack keep their DRAM1 Gene Counts in genome_03+: a kept
    # row also carries covered IDs, whose other rows were dropped.
    comparable = sorted(
        (names.genomes[row["fasta"]], kind, value)
        for row in kept
        if row["fasta"] not in keep
        for kind, value in row_ids(row) - covered
    )
    write_tsv(
        out / "comparable_ids.tsv",
        ["input_fasta", "id_type", "id"],
        [
            dict(zip(["input_fasta", "id_type", "id"], c))
            for c in dict.fromkeys(comparable)
        ],
    )
    write_tsv(
        out / "annotations.tsv", DRAM2_COLUMNS, [convert(row, names) for row in kept]
    )
    return names


def anonymize_trnas(annotate, out, names):
    """DRAM1 trnas.tsv -> DRAM2 trnas/raw_trna_scan.tsv (a directory, as --trnas takes), plus the pipeline's collected_trnas.tsv."""
    _, rows = read_tsv(annotate / "trnas.tsv")
    trnas = []
    for row in rows:
        genome = row["fasta"]
        scaffold = row["Name"].strip().removeprefix(f"{genome}_")
        trnas.append(
            {
                "input_fasta": names.genomes[genome],
                "query_id": names.scaffold(genome, scaffold),
                "tRNA #": row["tRNA #"],
                "begin": row["Begin"],
                "end": row["End"],
                "type": row["Type"],
                "codon": row["Codon"],
                "score": row["Score"],
                "note": row["Note"],
                "gene_id": f"{row['Type']} ({row['Codon']})",
            }
        )
    (out / "trnas").mkdir(exist_ok=True)
    write_tsv(out / "trnas/raw_trna_scan.tsv", TRNA_COLUMNS, trnas)
    collect = Path(__file__).resolve().parents[2] / "bin/trna_collect.py"
    with tempfile.TemporaryDirectory() as work:
        shutil.copy(out / "trnas/raw_trna_scan.tsv", work)
        subprocess.run([sys.executable, collect], cwd=work, check=True)
        shutil.copy(Path(work) / "collected_trnas.tsv", out)


def anonymize_distill(distill, out, names):
    """Rename genomes and scaffolds in DRAM1's distill outputs (all six genomes kept)."""
    import openpyxl

    for name in ["genome_stats.tsv", "product.tsv"]:
        (out / name).write_text(names.text((distill / name).read_text()))
    book = openpyxl.load_workbook(distill / "metabolism_summary.xlsx")
    for sheet in book.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    cell.value = names.text(cell.value)
    book.save(out / "metabolism_summary.xlsx")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--annotate", required=True, help="DRAM1 annotate output folder"
    )
    parser.add_argument("--distill", help="DRAM1 distill output folder")
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--keep",
        action="append",
        required=True,
        help="genome kept whole; give exactly two (they become genome_01 and genome_02)",
    )
    args = parser.parse_args(argv)
    annotate, out = Path(args.annotate), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if len(args.keep) != 2:
        parser.error("give --keep exactly twice")
    names = anonymize_annotations(annotate, out, args.keep)
    if (annotate / "trnas.tsv").exists():
        anonymize_trnas(annotate, out, names)
    if args.distill:
        anonymize_distill(Path(args.distill), out, names)


if __name__ == "__main__":
    main()
