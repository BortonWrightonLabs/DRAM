#!/usr/bin/env python
"""Value comparator for Summarize, Traits and Visualize outputs.

Reads a pipeline --outdir and reduces it to values:

- Summarize: Gene Count per (label, Genome), from `summarized_genomes.tsv` (today) or
  `summarize/*_summary.tsv` (Refine). Group, description, sheet, file name and order
  are ignored.
- Traits and Visualize: Presence or Coverage per (Rule, sheet, Genome), from the
  `df_vertical_genome*.tsv` tables both layouts write.

Only non-zero values are kept, so a missing value means 0 / absent.

    refine_values.py extract OUTDIR VALUES.tsv
    refine_values.py check OUTDIR BASELINE.tsv --check NAME --allowlist ALLOWLIST.tsv
    refine_values.py dram1 OUTDIR DRAM1_DIR --check NAME --allowlist ALLOWLIST.tsv
"""

import argparse
import csv
import sys
from pathlib import Path

VALUE_COLUMNS = ["kind", "sheet", "label", "genome", "value"]
# Summarize columns that are not a Genome; the first column is the label
SUMMARY_METADATA = {
    "gene_description",
    "topic_ecosystem",
    "module",
    "workbook",
    "header",
    "subheader",
    "category",
    "subcategory",
}
# genome_01/02 are whole genomes; genome_03-06 hold only some genes (tests/data/dram1/README.md)
DRAM1_WHOLE = {"genome_01", "genome_02"}


def read_tsv(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def label(text):
    """Summarize quotes some labels as rule expressions (`Ala (CGC)`); compare them bare.

    Whitespace is kept: a sheet's "K07304 " counts 0 where "K07304" counts 1.
    """
    return text.strip("`")


def gene_counts(outdir):
    """{(label, genome): Gene Count} from every Summarize table under outdir."""
    tables = [*outdir.rglob("summarized_genomes.tsv")]
    tables += [p for p in outdir.rglob("*_summary.tsv") if p.parent.name == "summarize"]
    counts = {}
    for table in tables:
        rows = read_tsv(table)
        if not rows:
            continue
        columns = list(rows[0])
        genomes = [c for c in columns[1:] if c not in SUMMARY_METADATA]
        for row in rows:
            for genome in genomes:
                key = (label(row[columns[0]]), genome)
                value = int(float(row[genome] or 0))
                if counts.setdefault(key, value) != value:
                    raise ValueError(
                        f"{key}: Gene Count {counts[key]} and {value} in {table}"
                    )
    return counts


def sheet(path, outdir):
    """The Refinement and sheet a df_vertical_genome table belongs to, in either layout.

    Today: TRAITS publishes SUMMARIZE/df_vertical_genome.tsv and PRODUCT_HEATMAP
    VISUALIZE/df_vertical_genome_<sheet>.tsv. Refine: traits/[<sheet>/] and visualize/<sheet>/.
    """
    parts = [p.lower() for p in path.relative_to(outdir).parts[:-1]]
    suffix = path.stem.removeprefix("df_vertical_genome").lstrip("_").lower()
    if "traits" in parts:
        below = parts[parts.index("traits") + 1 :]
        name = below[0] if below else ""
        return "traits" if name in ("", "default") else f"traits/{name}"
    if "visualize" in parts and parts[-1] != "visualize":  # Refine: visualize/<sheet>/
        return f"visualize/{parts[-1]}"
    if parts and parts[-1] == "summarize":  # today's TRAITS
        return "traits"
    return f"visualize/{suffix or 'custom'}"


def rule_values(outdir):
    """{(kind, sheet, rule, genome): value} for Presence and Coverage.

    shortcut: ignores dram-rules' `value` column (Sample Abundance, written only with a
    --mapping file, which no test passes); read it if a test adds one.
    """
    values = {}
    for table in outdir.rglob("df_vertical_genome*.tsv"):
        name = sheet(table, outdir)
        for row in read_tsv(table):
            key = (name, row["name"], row["genome"])
            if row.get("coverage_percentage"):
                values[("coverage", *key)] = round(float(row["coverage_percentage"]), 4)
            if row.get("present"):
                values[("presence", *key)] = row["present"].lower() == "true"
    return values


def extract(outdir):
    """Every non-zero value under outdir, keyed (kind, sheet, label, genome)."""
    outdir = Path(outdir)
    values = {("gene_count", "", *k): v for k, v in gene_counts(outdir).items()}
    values |= rule_values(outdir)
    return {k: v for k, v in values.items() if v}


def write_values(values, path):
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(VALUE_COLUMNS)
        for key in sorted(values):
            writer.writerow([*key, values[key]])


def read_values(path):
    def parse(kind, text):
        if kind == "presence":
            return text == "True"
        return int(text) if kind == "gene_count" else float(text)

    return {
        (r["kind"], r["sheet"], r["label"], r["genome"]): parse(r["kind"], r["value"])
        for r in read_tsv(path)
    }


def key_id(key):
    """Allowlist id: kind|sheet|label|genome."""
    return "|".join(key)


def allowlisted(path, check):
    return {r["id"] for r in read_tsv(path) if r["check"] == check}


def differences(actual, expected, keys=None):
    """{key: (expected, actual)} where they differ; a missing value is 0."""
    keys = set(actual) | set(expected) if keys is None else keys
    return {
        k: (expected.get(k, 0), actual.get(k, 0))
        for k in sorted(keys)
        if expected.get(k, 0) != actual.get(k, 0)
    }


def report(diffs, allowed):
    """Fail on any difference not allowlisted, and on any allowlisted one that went away."""
    unexplained = {k: v for k, v in diffs.items() if key_id(k) not in allowed}
    stale = allowed - {key_id(k) for k in diffs}
    for k, (expected, actual) in unexplained.items():
        print(f"differs: {key_id(k)}: expected {expected}, got {actual}")
    for k in sorted(stale):
        print(f"allowlisted but no longer differs: {k}")
    return not unexplained and not stale


def dram1_counts(dram1):
    """DRAM1 metabolism_summary.xlsx -> {(label, genome): Gene Count} for comparable values.

    genome_03-06 count only the IDs in comparable_ids.tsv. tRNAs come from every
    genome, so they are comparable everywhere; rRNAs aren't in the fixture.
    """
    import openpyxl  # only the dram1 command reads xlsx

    comparable = {
        (r["input_fasta"], r["id"]) for r in read_tsv(dram1 / "comparable_ids.tsv")
    }
    book = openpyxl.load_workbook(dram1 / "metabolism_summary.xlsx", read_only=True)
    counts = {}
    for ws in book.worksheets:
        if ws.title == "rRNA":
            continue
        rows = ws.iter_rows(values_only=True)
        header = next(rows)
        genomes = [c for c in header if c.startswith("genome_")]
        for row in rows:
            row = dict(zip(header, row))
            gene = label(row["gene_id"])
            for genome in genomes:
                if (
                    genome in DRAM1_WHOLE
                    or (genome, gene) in comparable
                    or ws.title == "tRNA"
                ):
                    counts[(gene, genome)] = int(float(row[genome]))
    return counts


def check_dram1(outdir, dram1):
    """{key: (DRAM1, DRAM2)} for Gene Counts that differ, over labels both report."""
    dram2 = gene_counts(Path(outdir))
    dram1 = dram1_counts(Path(dram1))
    dram2_labels = {gene for gene, _ in dram2}
    shared = {k for k in dram1 if k[0] in dram2_labels}
    diffs = differences(dram2, dram1, shared)
    return {("gene_count", "", *k): v for k, v in diffs.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract", help="write OUTDIR's values to VALUES.tsv")
    p.add_argument("outdir", type=Path)
    p.add_argument("values", type=Path)
    for name, other in [("check", "baseline"), ("dram1", "dram1_dir")]:
        p = sub.add_parser(name)
        p.add_argument("outdir", type=Path)
        p.add_argument(other, type=Path)
        p.add_argument("--check", required=True, help="allowlist check name")
        p.add_argument("--allowlist", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "extract":
        write_values(extract(args.outdir), args.values)
        return 0
    if args.command == "check":
        diffs = differences(extract(args.outdir), read_values(args.baseline))
    else:
        diffs = check_dram1(args.outdir, args.dram1_dir)
    if report(diffs, allowlisted(args.allowlist, args.check)):
        return 0
    if args.command == "check":
        print(
            f"re-record if intended: pixi run python {Path(__file__)} extract {args.outdir} {args.baseline}"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
