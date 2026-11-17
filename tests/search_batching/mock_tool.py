#!/usr/bin/env python3
"""Tiny stand-ins: verify real module command arguments and staging, not biology."""

import os
import re
import subprocess
import sys
from pathlib import Path

args = sys.argv[1:]
tool = Path(sys.argv[0]).name


def option(name):
    return args[args.index(name) + 1]


def sample(path):
    with open(path) as handle:
        return handle.readline().strip()


if tool == "sbatch":
    script = Path(args[-1]).resolve()
    contents = script.read_text()
    array = re.search(r"^#SBATCH --array[= ](\d+)-(\d+)", contents, re.MULTILINE)
    indices = range(int(array[1]), int(array[2]) + 1) if array else [None]
    job_id = str(os.getpid())
    log = Path(os.environ["MOCK_SLURM_LOG"])
    with log.open("a") as handle:
        handle.write(("array" if array else "single") + "\t" + str(script) + "\n")
    for index in indices:
        env = dict(os.environ, SLURM_JOB_ID=job_id)
        if index is not None:
            env.update(SLURM_ARRAY_JOB_ID=job_id, SLURM_ARRAY_TASK_ID=str(index))
        # Submission succeeds even when a child fails; Nextflow reads its exit file.
        subprocess.run(
            ["bash", str(script)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    print("Submitted batch job " + job_id)
elif tool in ["squeue", "scancel"]:
    pass  # All mock jobs finish synchronously during submission.
elif tool == "hmm_search.py":
    name = sample(option("--input_file"))
    assert Path(option("--hmm")).exists()
    assert int(option("--cpus")) >= 1
    if os.environ.get("FAIL_SAMPLE") == name:
        sys.exit(42)
    Path(option("--output_file")).write_text(name + "\n")
elif tool == "hmm_parser.py":
    name = sample(option("--hmm_domtbl"))
    assert sample(option("--gene_locs")) == name
    if name != "nohit":
        Path(option("--output")).write_text(name + ":" + option("--db_name") + "\n")
elif tool == "mmseqs":
    if args[0] == "createdb":
        Path(args[2]).write_text(sample(args[1]) + "\n")
        # real createdb also writes <db>.index
        Path(args[2] + ".index").write_text(sample(args[1]) + "\n")
    elif args[0] == "createindex":
        assert option("--threads") == "1"
        Path(args[1] + ".index").write_text(sample(args[1]) + "\n")
    elif args[0] == "search":
        name = sample(args[1])
        assert Path(args[1] + ".index").exists()
        assert Path(args[2]).exists()
        if os.environ.get("FAIL_SAMPLE") == name:
            sys.exit(42)
        Path(args[3]).write_text(name + "\n")
    elif args[0] == "convertalis":
        name = sample(args[1])
        assert sample(args[3]) == name
        Path(args[4]).write_text("" if name == "nohit" else name + "\n")
    elif args[0] == "filterdb":
        # every filterdb flag DRAM uses takes a value; the positionals are in, out
        positional = [
            a
            for i, a in enumerate(args[1:], 1)
            if not a.startswith("--") and not args[i - 1].startswith("--")
        ]
        Path(positional[1]).write_text(Path(positional[0]).read_text())
    elif args[0] != "rmdb":
        raise AssertionError(args)
elif tool == "mmseqs_add_descriptions.py":
    name, db, info, bitscore, loci, raw, output = args
    assert sample(loci) == name
    assert sample(raw) == name
    Path(output).write_text(name + ":" + db + "\n")
else:
    raise AssertionError(tool)
