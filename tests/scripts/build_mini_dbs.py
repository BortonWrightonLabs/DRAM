#!/usr/bin/env python3
"""Build the tiny test databases in tests/data/db/ from the full DRAM databases."""

import argparse
import csv
import gzip
from pathlib import Path
import subprocess
import tarfile
import tempfile
from typing import NamedTuple


def hmm_records(handle):
    """Yield (name, record text) for each record of a text HMM stream."""
    record, name = [], None
    for line in handle:
        record.append(line)
        if line.startswith("NAME  "):
            name = line.split()[1]
        elif line.startswith("//"):
            yield name, "".join(record)
            record, name = [], None


def subset_hmm(source, names):
    """Return the records of the text HMM file `source` whose NAME is in `names`, in file order.

    File order matters: hit lists such as fegenie_ids follow database order.
    """
    wanted = set(names)
    with open(source) as handle:
        kept = [(name, text) for name, text in hmm_records(handle) if name in wanted]
    require_all(wanted, {name for name, _ in kept}, source)
    return "".join(text for _, text in kept)


def require_all(wanted, found, source):
    missing = set(wanted) - set(found)
    if missing:
        raise ValueError(f"not in {Path(source).name}: {', '.join(sorted(missing))}")


def subset_rows(source, ids):
    """Return the header plus rows of a TSV (optionally .gz) whose first field is in `ids`."""
    opener = gzip.open if str(source).endswith(".gz") else open
    with opener(source, "rt") as handle:
        header = next(handle)
        return header + "".join(
            line for line in handle if line.split("\t", 1)[0] in ids
        )


def read_ids(folder):
    return set((Path(folder) / "ids.txt").read_text().split())


def build_kofam(profiles, ko_list, out):
    """Write out/kofam.hmm and out/kofam_ko_list.tsv for the KOs in out/ids.txt.

    `profiles` is the GenomeNet profiles.tar.gz (one profiles/K*.hmm per KO)
    or a local concatenated kofam_profiles.hmm. Records are written in ids.txt
    order, which `select` takes from the full database: hit lists such as
    kofam_ids follow it, and the release tarball doesn't record it.
    """
    out = Path(out)
    order = (out / "ids.txt").read_text().split()
    ids = set(order)
    if str(profiles).endswith((".tar.gz", ".tgz")):
        found = {}
        with tarfile.open(profiles) as tar:
            for member in tar:
                ko = Path(member.name).stem
                if member.name.endswith(".hmm") and ko in ids:
                    found[ko] = tar.extractfile(member).read().decode()
    else:
        with open(profiles) as handle:
            found = {name: text for name, text in hmm_records(handle) if name in ids}
    require_all(ids, found, profiles)
    hmm = "".join(found[ko] for ko in order)
    (out / "kofam.hmm").write_text(hmm)
    (out / "kofam_ko_list.tsv").write_text(subset_rows(ko_list, ids))


class HmmDb(NamedTuple):
    source: str  # under databases/
    table: str | None  # score/threshold table the pipeline passes to hmm_parser
    mode: str  # how to choose models, see below
    e_value: (
        float | None
    )  # the pipeline's hmmsearch e-value for this database (nextflow.config)


# "hits":      keep every model with a hit within the pipeline's e-value, so the mini
#              database gives the same annotations as the full one.
# "threshold": as "hits", but only models that also pass the table's threshold (the only ones
#              the pipeline reports), plus a few near misses that fail it.
# "near":      the database gives OWC no annotations; keep the best-scoring models that are
#              still within the e-value, so the "scored but below threshold" path runs.
# Every HMM database also keeps a few small models OWC never scores against (decoys).
# mmseqs databases keep each OWC gene's top 5 targets by bit score, plus decoys.
HMM_DBS = {
    "kofam": HmmDb(
        "kofam/kofam_profiles.hmm", "kofam/kofam_ko_list.tsv", "threshold", 1e-5
    ),
    "vogdb": HmmDb("vogdb/vog_latest_hmms.hmm", None, "hits", 1e-5),
    "fegenie": HmmDb("fegenie/fegenie.hmm", None, "hits", 1e-5),
    "camper_hmm": HmmDb(
        "camper/hmm/camper.hmm", "camper/hmm/camper_hmm_scores.tsv", "near", 1e-5
    ),
    "canthyd_hmm": HmmDb(
        "canthyd/hmm/cant_hyd.hmm", "canthyd/hmm/cant_hyd_HMM_scores.tsv", "near", 1e-5
    ),
    # the pipeline runs dram_db with no e-value cutoff (HMM_DRAM_DB in db_search.nf)
    "dram_db": HmmDb("dram_db/dram_db.hmm", "dram_db/dram_db_scores.tsv", "near", None),
}
MMSEQS_DBS = {
    "uniref": ("uniref/uniref.mmsdb", None),
    "canthyd_mmseqs": (
        "canthyd/mmseqs/cant_hyd.mmsdb",
        "canthyd/mmseqs/cant_hyd_BLAST_scores.tsv",
    ),
    "camper_mmseqs": ("camper/mmseqs/camper.mmsdb", "camper/mmseqs/camper_scores.tsv"),
}
NEAR_MISSES = 3
TOP_TARGETS = 5
DECOYS = 3


def passes_threshold(row, full, domain):
    """hmm_parser's rule: the full or best domain score must reach the model's threshold."""
    try:
        threshold = float(row["threshold"])
    except ValueError:  # "-": KOfam gives no threshold, so the e-value alone decides
        return True
    return (domain if row["score_type"] == "domain" else full) >= threshold


def select_hmm(source, proteins, mode, e_value, table=None):
    """Return the model names to keep from `source` for OWC `proteins` (one FASTA per sample)."""
    import pyhmmer

    best = {}  # name -> [best full score, best domain score, best e-value]
    lengths = {}
    for fasta in proteins:  # one search per sample, as the pipeline does
        with pyhmmer.easel.SequenceFile(fasta, digital=True) as handle:
            seqs = handle.read_block()
        with pyhmmer.plan7.HMMFile(source) as hmms:
            for hits in pyhmmer.hmmer.hmmsearch(hmms, seqs, cpus=8):
                name = hits.query.name
                name = name.decode() if isinstance(name, bytes) else name
                lengths[name] = hits.query.M
                for hit in hits:
                    scores = best.setdefault(
                        name, [float("-inf"), float("-inf"), float("inf")]
                    )
                    scores[0] = max(scores[0], hit.score)
                    scores[1] = max(
                        [scores[1], *(domain.score for domain in hit.domains)]
                    )
                    scores[2] = min(scores[2], hit.evalue)
    # hmm_search.py drops hits outside the e-value before hmm_parser ever sees them
    reported = [name for name in best if e_value is None or best[name][2] <= e_value]
    by_score = sorted(reported, key=lambda name: (-best[name][0], name))
    if mode == "near":
        keep = set(by_score[:NEAR_MISSES])
    else:
        keep = set(reported)
        if mode == "threshold":
            with open(table) as handle:
                rows = {
                    row["knum"]: row for row in csv.DictReader(handle, delimiter="\t")
                }
            keep = {
                name for name in keep if passes_threshold(rows[name], *best[name][:2])
            }
            keep |= set([name for name in by_score if name not in keep][:NEAR_MISSES])
    unscored = sorted((lengths[name], name) for name in lengths if name not in best)
    keep |= {name for _, name in unscored[:DECOYS]}
    return [name for name in lengths if name in keep]  # database order, see build_kofam


def mmseqs(*args, cwd):
    subprocess.run(["mmseqs", *map(str, args), "-v", "1"], cwd=cwd, check=True)


def select_mmseqs(source, proteins, work):
    """Return the target accessions to keep from mmseqs database `source`."""
    work = Path(work)
    query = work / "query.faa"
    query.write_text("".join(Path(p).read_text() for p in proteins))
    mmseqs("createdb", query, "query.mmsdb", cwd=work)
    mmseqs(
        "search", "query.mmsdb", source, "result", "tmp", "--threads", "16", cwd=work
    )
    mmseqs(
        "convertalis",
        "query.mmsdb",
        source,
        "result",
        "hits.tsv",
        "--format-output",
        "query,target,bits",
        cwd=work,
    )
    by_query = {}
    for line in (work / "hits.tsv").read_text().splitlines():
        query_id, target, bits = line.split("\t")
        by_query.setdefault(query_id, []).append((-float(bits), target))
    keep = {
        target for hits in by_query.values() for _, target in sorted(hits)[:TOP_TARGETS]
    }
    hit = {target for hits in by_query.values() for _, target in hits}
    decoys = []
    with open(f"{source}.lookup") as lookup:
        for line in lookup:
            accession = line.split("\t")[1]
            if accession not in hit:  # OWC never matches a decoy
                decoys.append(accession)
            if len(decoys) == DECOYS:
                break
    return keep | set(decoys)


def build_mmseqs(source, ids, out, work):
    """Write out/<name>.faa (sorted) and an mmseqs database built from it."""
    work, out = Path(work), Path(out)
    with open(f"{source}.lookup") as lookup:
        keys = [line.split("\t")[0] for line in lookup if line.split("\t")[1] in ids]
    (work / "keys.txt").write_text("\n".join(keys) + "\n")
    mmseqs("createsubdb", "keys.txt", source, "sub", cwd=work)
    mmseqs("createsubdb", "keys.txt", f"{source}_h", "sub_h", cwd=work)
    mmseqs("convert2fasta", "sub", "sub.faa", cwd=work)
    records = (work / "sub.faa").read_text().split(">")[1:]
    name = Path(source).stem
    fasta = out / f"{name}.faa"
    fasta.write_text(
        "".join(">" + r for r in sorted(records, key=lambda r: r.split()[0]))
    )
    for old in out.glob(f"{name}.mmsdb*"):
        old.unlink()
    mmseqs("createdb", fasta.name, f"{name}.mmsdb", cwd=out)


def build(databases, out):
    """Write every committed mini database from the ids.txt files under `out`."""
    databases, out = Path(databases).resolve(), Path(out)
    for folder, (source, table, _, _) in HMM_DBS.items():
        if folder == "kofam":
            continue  # licence unclear: built locally or in CI by `kofam`, never committed
        ids = read_ids(out / folder)
        (out / folder / Path(source).name).write_text(
            subset_hmm(databases / source, ids)
        )
        if table:
            (out / folder / Path(table).name).write_text(
                subset_rows(databases / table, ids)
            )
    for folder, (source, table) in MMSEQS_DBS.items():
        ids = read_ids(out / folder)
        with tempfile.TemporaryDirectory() as work:
            build_mmseqs(databases / source, ids, out / folder, work)
        if table:
            # CAMPER accessions are "D00014;CarE"; its score table is keyed by "D00014"
            keys = ids | {accession.split(";")[0] for accession in ids}
            (out / folder / Path(table).name).write_text(
                subset_rows(databases / table, keys)
            )


def select(databases, proteins, out):
    """Search OWC against the full databases, write each ids.txt, then build."""
    databases, out = Path(databases), Path(out)
    for folder, db in HMM_DBS.items():
        table = db.table and databases / db.table
        ids = select_hmm(databases / db.source, proteins, db.mode, db.e_value, table)
        (out / folder).mkdir(parents=True, exist_ok=True)
        (out / folder / "ids.txt").write_text("\n".join(ids) + "\n")
    for folder, (source, _) in MMSEQS_DBS.items():
        with tempfile.TemporaryDirectory() as work:
            ids = select_mmseqs((databases / source).resolve(), proteins, work)
        (out / folder).mkdir(parents=True, exist_ok=True)
        (out / folder / "ids.txt").write_text("\n".join(sorted(ids)) + "\n")
    build(databases, out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    kofam = commands.add_parser("kofam", help="build the KOfam subset from its ids.txt")
    kofam.add_argument(
        "--profiles", required=True, help="profiles.tar.gz or kofam_profiles.hmm"
    )
    kofam.add_argument(
        "--ko-list", required=True, help="ko_list(.gz) or kofam_ko_list.tsv"
    )
    kofam.add_argument("--out", required=True, help="folder holding ids.txt")
    for name, helptext in [
        ("select", "search OWC against databases/, rewrite every ids.txt, then build"),
        ("build", "rebuild the committed mini databases from their ids.txt"),
    ]:
        command = commands.add_parser(name, help=helptext)
        command.add_argument("--databases", default="databases")
        command.add_argument("--out", default="tests/data/db")
        if name == "select":
            command.add_argument(
                "--proteins",
                nargs="+",
                default=sorted(Path("tests/data/owc/called_genes").glob("*.faa")),
            )
    args = parser.parse_args(argv)
    if args.command == "kofam":
        build_kofam(args.profiles, args.ko_list, args.out)
    elif args.command == "build":
        build(args.databases, args.out)
    else:
        select(args.databases, args.proteins, args.out)


if __name__ == "__main__":
    main()
