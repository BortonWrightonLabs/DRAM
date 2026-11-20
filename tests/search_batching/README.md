# Search batching regression tests

Run from the repository root with an installed Nextflow and Python 3:

```bash
NXF_VER=25.04.7 python3 -m unittest discover -s tests/search_batching -v
NXF_VER=25.10.0 python3 -m unittest discover -s tests/search_batching -v
```

These tests execute the production MMseqs search workflows plus generated task scripts with small mock search executables. They verify staging, per-sample output association, missing optional outputs, class routing, deterministic batching, the per-input size cutoff, resource caps, database-specific selectors, failure propagation, and resume. Sparse query files exercise medium and large classes without allocating gigabytes of data. Oversized sparse database files confirm that database size does not affect batching or resource classification.

The array test uses a local Slurm stand-in (`sbatch`, `squeue`, and `scancel`) to execute Nextflow's generated array dispatch scripts. It never submits cluster jobs. This checks workflow/array integration, not real Slurm scheduling policy or biological search accuracy. Each test uses and cleans up an isolated temporary directory. Nextflow versions must already be installed when running offline.
