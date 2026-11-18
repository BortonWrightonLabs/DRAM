# DRAM: Contribution

Hi there!
Many thanks for taking an interest in improving DRAM.

DRAM is written as a Nextflow Pipeline that wraps around the largely python code that does the DRAM calculations. Nextflow handles a lot of the cross platform deployment, dependency manegement, scheduling, and parallelization. What we need to do to get that out of Nextflow though is write whatever DRAM python code we need that can be interphased with through a CLI so Nextflow can call it directly by passing arguements to it. Then the script should write its outputs to files so Nextflow can pass those arguments to the next step.

## Nextflow resources

You can read more about Nextflow [here](https://www.nextflow.io/docs/latest/index.html),

## Nf-core

DRAM is also following the convention of the nf-core community, which is a a large community bioinformatics Nextflow users that have developed tools and standards for using Nextflow and making it easier to use Nextflow. DRAM is currectly still in the process of transition from the original Nextflow implementation of DRAM to the nf-core style DRAM which will allows more flexibility and easier development.

nf-core docs, tools, and examples can be found [here](https://nf-co.re/docs/)

## Main Structure of DRAM with Nextflow

Pipeline kicks of with `main.nf` which runs some boiler plate initialization steps such as printing the help text if needed, prints your parameters you are using, etc. Then calls the main DRAM pipeline file, which is `workflows/dram.nf`. `workflows/dram.nf` controls the entire flow of the steps of DRAM. Every pipeline step we think of in DRAM runs through this file to some extect. Call Prodigal, Annotate, Distill, Product, etc. When DRAM wants to run Annotate, because Annotate is a large step with many substeps, it then calls `subworkflows/local/annotate.nf`, which then does all of the logic for the Annotate step. Annotate then calls individual processes such as `modules/local/annotate/mmseqs_index.nf` which is then dispatched with the scheduler (SLURM if you are using SLURM, or whatever other scheduling system you are using (local, or whatever)). Those individual processes that get dispatched as individual jobs (or parallel jobs) are what run the DRAM python and other language scripts.

## Pipeline contribution conventions

HMM and MMseqs database searches should invoke `HMM_SEARCH_WORKFLOW` or `MMSEQS_SEARCH_WORKFLOW` from `subworkflows/local`, aliased once per database in `db_search.nf`. These wrappers own batching, resource-class branching, and restoring per-sample outputs. Keep their internal `SEARCH_SMALL`, `SEARCH_MEDIUM`, and `SEARCH_LARGE` processes separate so job arrays have uniform initial requests. Shared search and FASTA batching helpers live in `utils_batches.nf`.

The [search batching regression tests](https://github.com/BortonWrightonLabs/DRAM/blob/dev/tests/search_batching/README.md) run the production workflows and generated scripts with mock search and Slurm executables on Nextflow 25.04 and 25.10. Run them when changing search inputs, staging, output channels, or resource policies.

CALL_GENES, TRNA_SCAN, and RRNA_SCAN use the FASTA adapters from `utils_batches.nf`. Keep gene calling, tRNA scanning, and rRNA scanning as separate process families, and restore batched results to per-sample channels before downstream collection. Their [preprocessing batching regression tests](https://github.com/BortonWrightonLabs/DRAM/blob/dev/tests/preprocessing_batching/README.md) cover generated scripts, resource classes, arrays, caching, and failures on Nextflow 25.04 and 25.10.

Carry logical workload bytes with a sample's channel tuple once an artifact is final: input FASTA after decompression/renaming, called protein FASTA after CALL, and filtered FASTA after CALL. Do not use a mutable global map or recompute size in every database wrapper. In particular, MMseqs indexing must preserve the called-protein byte count; generated index-file size is not a scheduling input.

To make the DRAM code and processing logic more understandable for new contributors and to ensure quality, we semi-standardise the way the code and other contributions are written.

### Prefer what can't go stale

Rely on things that stay correct on their own over things someone has to remember to update. Hand-kept lists of process names, image tags, file paths or versions, or copies of another tool's internal rules, quietly drift when code, people or tools change. When they do, someone loses time working out why the thing exists, what it should now say and how to fix it.

- Derive values from the source of truth (the code, the config, the tool's own output) at the point of use, instead of keeping a copy.
- Prefer the tool's own behaviour (a cache directory, a retry setting) over a script that re-implements part of it.
- If a hand-kept piece is unavoidable, make drift fail loudly with a clear message, and say in a comment what it must match and why it exists.

### Adding a new step

1. Write up your main script or script code in whatever language and place it in the bin folder.
   - We need to ensure it is executable for Nextflow, so add a shebang to the top of the file (ex. `#!/usr/bin/env python` for a python file) then run `chmod a+x bin/new_script.py` replacing new_sciprt.py with the actual script.
1. If this is a new process, add a new nextflow script (`.nf`) under `modules/local/whatever_subdir_it_goes`
1. Define the corresponding input channels and output channels
1. If your scripts in the `bin` folder need external dependencies (such as from conda), then add a `environment.yml` file in the same directory as your process (in the `module/local/..`) in your process script add `conda "${moduleDir}/environment.yml"` above your input channels. (See other process scripts as examples).
1. You will now need to install the wave-cli tool to create containers on demand from conda environments. This is how we specify our containers without having to manage docker files or anything else like that. Wave just tells Nextflow how to pull a container on demand from a conda file. You can install wave-cli [here](https://github.com/seqeralabs/wave-cli). Ideally this will be integrated into our CI/CI system in the future.
1. Once you have Wave installed, create both OCI and native Singularity images from the module environment:
   - `wave --freeze --conda-file modules/local/subdir/environment.yml`
   - `wave --singularity --freeze --conda-file modules/local/subdir/environment.yml`
   Add both returned URIs to the module's `container` directive, selecting the `oras://` URI when `workflow.containerEngine` is `singularity` or `apptainer`.
   - Now users can run DRAM with with `-profile conda` and `-profile singulary/docker/apptainer/etc.` and it will just work without them installing the dependencies
1. Add an intrinsic computation label in the process definition. Reuse `process_small`, `process_medium`, and the other generic labels when a fixed default is appropriate. Input-sensitive tools should use a semantic label such as `process_mmseqs_search`, with their shared resource policy defined in `conf/base.config`. Add `process_array` only when all initial tasks in each process invocation have uniform scheduler directives. Users can override these labels in their own configuration files.
1. Add your process by name to `conf/modules.config` if you want to change where your output files get stored in the user's outdir.
1. Add a script section to call your DRAM script, passing in whatever CLI argumenets. The outputs from your DRAM script should be the process outputs. You want them to be written directly in the working directory, Nextflow will manage moving them to the users output directy. You can also rename outputs for future Nextflow steps with the `emit:` keyword, and mark some outputs as optional (see other processes).
1. We now need to add this process to the correct part in our pipeline to be called and ran. If it is in an already established step such as Annotate, we might go to `subworkflows/local/annotate.nf` and find the right spot in that code and add it. Though we might need to add a new subworkflow and add that to our `workflows/dram.nf`
1. We also need to add any new parameters to our `nextflow.config` with a default. And then add the equivalent parameter to our `nextflow_schema.json` with help text. The `nextflow_schema.json` is how our `--help` CLI option is populated as well as what our parameters page on our docs is built from. It also allows us to add sanity checks and validation for all relevant parameters.

## Contribution workflow

1. Branch off `dev`.
1. Open a PR into `dev` with a [Conventional Commit](https://www.conventionalcommits.org/) title (`feat: …`, `fix: …`, `docs: …`). The `conventional-title` check enforces it, and the changelog is built from these titles (`cliff.toml`):
   - `style:` is for formatting only and stays out of the changelog. A formatting commit with another type can be listed in `.git-blame-ignore-revs`, which git-cliff (2.14.1+) and `git blame` both skip.
   - `fix(internal):` is a fix users of the pipeline can't see (code, not results or interface). It goes under an Internal subheading of Bug Fixes. If a change could alter outputs, make it a plain `fix:`, and split mixed changes into separate PRs.
   - A fix for a bug that hasn't been released yet ends its message with a `Fixes: <sha>` trailer naming the commit that introduced it. The changelog leaves it out when that commit is in the same release, since users never saw the bug.
1. Keep separate commits while the PR is in review. When it's ready to merge, squash the branch into one commit whose message describes the whole change: PRs into `dev` are squash merged, and with one commit the squash uses that commit's message.
1. CI (pre-commit and the PR test gate below) must pass. The test gate (`.github/workflows/tests.yml`) skips PRs that only change docs and other non-code files; pre-commit always runs.

## Testing

### Running the tests

The `pixi.toml` tasks run everything; [pixi](https://pixi.sh) provides Nextflow, nf-test, pytest and Python.

| Command | Runs | Needs |
|---|---|---|
| `pixi run test` | The PR gate: pytest, then nf-tests tagged `pr`. CI runs this. | the KOfam mini database (below) |
| `pixi run test-full` | nf-tests tagged `full` | the full `databases/` |
| `pixi run test-update` | the `pr` nf-tests, re-recording their snapshots | |

- Containers default to singularity (apptainer's `singularity` shim works too). Set `DRAM_ENGINE=docker` or `DRAM_ENGINE=apptainer` to switch.
- Arguments after the task go to nf-test, so one file runs with `pixi run test-nf tests/owc_pr.nf.test`.
- The KOfam mini database isn't committed. Build it once as described in [`tests/data/db/README.md`](https://github.com/BortonWrightonLabs/DRAM/blob/dev/tests/data/db/README.md).
- The search and preprocessing batching checks run separately; see their READMEs, linked under [Pipeline contribution conventions](#pipeline-contribution-conventions).

### What tests assert

Assert on published outputs (what lands in `--outdir`), not process names, inputs or channel shapes. A process rename or merge that leaves the outputs unchanged must not break a test.

### Where things live

| Path | What |
|---|---|
| `tests/python/` | pytest unit tests for `bin/` scripts and `tests/scripts/` |
| `tests/*.nf.test` | nf-test pipeline tests; `tests/pr.config` points the `pr` ones at the mini databases |
| `tests/data/owc/` | two OWC genomes and their expected annotations |
| `tests/data/db/` | mini databases built from what OWC hits; rebuilt with `tests/scripts/build_mini_dbs.py` |
| `tests/data/dram1/` | an anonymized DRAM1 run, built with `tests/scripts/anonymize_dram1.py` |
| `tests/data/synthetic/` | a hand-built annotations table for databases the other fixtures don't annotate |
| `tests/data/allowlist.tsv` | known differences, one reason per line |

Each `tests/data/*/README.md` describes its fixture: where it came from and what each part covers.

### When a test fails after your change

**Snapshot diff** (`tests/owc_pr.nf.test`): re-record with `pixi run test-update`, then review the `.snap` diff. Every changed line should follow from your change. Say why in the commit message.

**Value diff** (`tests/refine_values.nf.test`): `tests/scripts/refine_values.py` reduces Refine outputs to values: a Gene Count per (label, Genome) and a Presence or Coverage per (rule, sheet, Genome). File names, Groups, descriptions and row order are ignored, and only non-zero values are stored, so a label that disappears reads as 0. A failure prints each value that differs and the command to re-record. Explain every difference before deciding:

- **Re-record** when the reference is DRAM2's own earlier output (`baseline_values.tsv`) and every difference is intended. Use the command the failure prints, and put the explanation in the commit message. The baseline's `bin/rules` commit is the one in the commit that last changed it:

  ```sh
  git ls-tree "$(git log -1 --format=%h -- tests/data/dram1/baseline_values.tsv)" bin/rules
  ```

- **Allowlist** when the reference can't be re-recorded, such as DRAM1's outputs or expected annotations. Add one line to `tests/data/allowlist.tsv` per difference, with the reason. An allowlisted value that stops differing also fails, so remove its line.

### Bumping `bin/rules`

`bin/rules` is the dram-rules submodule that runs Refine.

1. Move it to the new commit and run `pixi run test`.
1. Trace each snapshot and value difference to a dram-rules commit (`git -C bin/rules log OLD..NEW`). A difference you can't trace is a bug, here or upstream.
1. Check that the differences are what those commits describe. For example, when labels are renamed, no Gene Count should change for a label present before and after.
1. Re-record the snapshot and baselines, and remove allowlist lines that no longer differ.
1. If dram-rules added or renamed a command-line option, mirror it in `nextflow.config`, `nextflow_schema.json`, `workflows/dram.nf` and `modules/local/refine/refine.nf`.
1. Summarize the differences and the commits they come from in the commit message.
