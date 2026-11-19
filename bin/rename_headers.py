#!/usr/bin/env python
"""Prefix every FASTA header with `<name>_`, skipping files that are already Renamed.

usage: rename_headers.py MANIFEST OUTDIR NAME FASTA [NAME FASTA ...]

Each output is OUTDIR/<name><input suffix>: a symlink to the input when every header
already starts with `<name>_`, otherwise a rewritten copy. MANIFEST gets one
`<name>\t<output filename>` line per input.
"""

import os
import sys
from pathlib import Path


def is_renamed(fasta, prefix):
    """True when every header starts with prefix; stops at the first one that doesn't."""
    with open(fasta) as fin:
        return all(line.startswith(prefix) for line in fin if line.startswith(">"))


def rename(fasta, out, prefix):
    """Write fasta to out with prefix on every header; return how many already had it."""
    already = 0
    with open(fasta) as fin, open(out, "w") as fout:
        for line in fin:
            if line.startswith(">"):
                already += line.startswith(prefix)
                line = f"{prefix}{line[1:]}"
            fout.write(line)
    return already


def main(manifest, outdir, *pairs):
    if not pairs or len(pairs) % 2:
        sys.exit("expected NAME FASTA pairs after MANIFEST OUTDIR")
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with open(manifest, "w") as man:
        for name, fasta in zip(pairs[::2], pairs[1::2]):
            out = outdir / f"{name}{Path(fasta).suffix}"
            prefix = f">{name}_"
            if is_renamed(fasta, prefix):
                print(f"{fasta}: already renamed, linking unchanged", file=sys.stderr)
                os.symlink(os.path.relpath(fasta, outdir), out)
            elif already := rename(fasta, out, prefix):
                print(
                    f"WARNING: {fasta}: {already} headers already started with "
                    f"'{prefix[1:]}' and are now prefixed twice",
                    file=sys.stderr,
                )
            man.write(f"{name}\t{out.name}\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
