#!/usr/bin/env python
import time
from contextlib import ExitStack
from itertools import chain
import pyhmmer
import click
from pathlib import Path

alphabet = pyhmmer.easel.Alphabet.amino()


@click.command()
@click.option(
    "--hmm",
    type=str,
    help="Path glob to the HMM db.",
)
@click.option(
    "--input_file",
    type=click.Path(exists=True),
    help="Path to the input fasta to search against",
)
@click.option("--e_value", type=float, help="e value cutoff for filtering")
@click.option("--t_value", type=float, help="bitscore cutoff for filtering")
@click.option(
    "--output_file",
    type=click.Path(),
    help="Path to output file",
)
@click.option("--cpus", type=int, help="number of cpu core to run HMMER with")
def main(hmm, input_file, e_value, t_value, output_file, cpus):
    t1 = time.time()

    hmm = Path(hmm)
    if hmm.is_dir():  # if directory passed, glob all hmms in dir
        hmm = hmm / "*.hmm"
    if "*" in str(hmm) or "?" in str(hmm):  # check if path is glob path
        hmm_paths = hmm.parent.glob(hmm.name)
    else:
        hmm_paths = [hmm]

    kw = {}
    if t_value:
        kw["T"] = t_value
    elif e_value:
        kw["E"] = e_value

    # Stream profiles into hmmsearch rather than holding them all (KOfam: 4.4 -> 1.4 GB peak).
    with ExitStack() as stack, open(output_file, "wb") as out_fh:
        hmms = chain.from_iterable(
            stack.enter_context(pyhmmer.plan7.HMMFile(path)) for path in hmm_paths
        )
        with pyhmmer.easel.SequenceFile(
            input_file, digital=True, alphabet=alphabet
        ) as sf:
            seqs = pyhmmer.easel.DigitalSequenceBlock(alphabet)
            seqs.extend(sf)
            first = True
            for hits in pyhmmer.hmmer.hmmsearch(hmms, seqs, cpus=cpus, **kw):
                hits.write(out_fh, format="domains", header=first)
                first = False
            # total = sum(len(hits) for hits in pyhmmer.hmmer.hmmsearch(hmms, seqs, cpus=8, E=1e-15))
            print(f"pyhmmer search completed in {time.time() - t1:.3} seconds")


if __name__ == "__main__":
    main()
