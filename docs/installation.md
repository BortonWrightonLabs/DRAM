# DRAM Installation Guide

## Requirements

- Nextflow **25.04.0 or newer**, as required by DRAM's `nextflow.config` manifest.
- A Java version supported by your chosen Nextflow release. See the [Nextflow installation requirements](https://www.nextflow.io/docs/stable/install.html).
- One container runtime: **Apptainer, Singularity CE, Docker, Podman, Shifter, or Charliecloud**. Alternatively, use **Conda or Mamba** to create software environments without containers. The selected runtime or environment manager must be installed and available on the nodes that execute tasks.
- Preformatted DRAM databases for the annotation databases you select.
- For SLURM, access to a submission host with `sbatch`, `squeue`, and `scancel`, an allocation if required, and shared storage accessible from compute nodes.

On HPC systems, Nextflow, Java, and Apptainer or Singularity are often provided through environment modules. Follow your cluster's documentation for loading them and for where long-running workflow drivers are allowed.

## Installation steps

### 1. Install Nextflow and a dependency runtime

Use your cluster's Nextflow module or follow the [Nextflow installation instructions](https://www.nextflow.io/docs/stable/install.html). Alternatively, install Nextflow through Conda:

```bash
conda create --name env_nf -c conda-forge -c bioconda 'nextflow>=25.04.0'
conda activate env_nf
nextflow -version
```

#### Available container runtimes

DRAM includes the following container profiles in its `nextflow.config`. Install or load the runtime available on your system, then select its matching profile when launching DRAM:

| Container runtime | Nextflow option |
| --- | --- |
| Apptainer | `-profile apptainer` |
| Singularity CE | `-profile singularity` |
| Docker | `-profile docker` |
| Podman | `-profile podman` |
| Shifter | `-profile shifter` |
| Charliecloud | `-profile charliecloud` |

Choose one container runtime profile per run. A profile configures Nextflow to use that runtime; it does not install the runtime itself. On an HPC system, use a runtime supported by your administrators and available on the compute nodes. Selecting SLURM is separate: for example, `-profile apptainer,slurm` uses Apptainer for software and SLURM for task submission.

Check that your chosen runtime is available, for example:

```bash
apptainer --version
```

#### Conda and Mamba alternatives

Conda and Mamba are environment managers, not container runtimes. Use `-profile conda` to create task environments with Conda, or `-profile mamba` to create them using Mamba. The latter requires Mamba to be installed. Choose one of these profiles instead of a container runtime profile. Installing Nextflow in a Conda environment does not require using the `conda` execution profile.

### 2. Prepare a launch directory and databases

Create a directory from which to launch your analyses:

```bash
mkdir -p dram-runs/databases
cd dram-runs
```

Download the preformatted databases you need through [Globus](https://app.globus.org/file-manager?origin_id=97ed64b9-dea0-4eb5-a7e0-0b50ac94e889) (collection UUID: `97ed64b9-dea0-4eb5-a7e0-0b50ac94e889`). You need a Globus account. Use the web interface for individual transfers or [Globus Connect Personal](https://docs.globus.org/globus-connect-personal/install/) for bulk transfers. Disk requirements depend on the databases selected. KEGG data must be obtained under the applicable KEGG access terms.

By default, database paths point into `databases/` under the **launch directory**, the directory where you start Nextflow. Shared databases can stay elsewhere: set their individual DRAM parameters in a config or parameters file. There is no single database-root parameter. For example, save this as `databases.config` and replace the paths:

```groovy
params {
    kegg_db = '/shared/DRAM/databases/kegg/'
    kofam_db = '/shared/DRAM/databases/kofam/'
    kofam_list = '/shared/DRAM/databases/kofam/kofam_ko_list.tsv'
}
```

Configure every database you enable, including any associated score/list/version files. See the [Parameters API](params_doc.md) for the full set of database paths. `--anno_dbs all` enables databases whose configured paths exist and warns and skips missing paths. An existing but incomplete database directory can still fail later. Explicit selections such as `--anno_dbs kofam` make the intended database set clear and require those databases to be available.

### 3. Download DRAM2

These examples use the `dev` branch for DRAM2:

```bash
nextflow pull BortonWrightonLabs/DRAM -r dev
```

Use the same revision when launching:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev --help
```

Update that branch with `nextflow pull BortonWrightonLabs/DRAM -r dev`. For reproducible analyses, replace `dev` with a DRAM2 release tag or commit in both commands. DRAM1 releases predate this Nextflow pipeline; do not use a DRAM1 revision with these instructions. Omitting `-r` uses the repository's default branch, which may differ from the DRAM2 development branch.

Nextflow caches the pipeline under `$NXF_HOME/assets/` (normally `$HOME/.nextflow/assets/`). You do not need to copy the pipeline's `nextflow.config` into your launch directory: it includes other repository files and is loaded automatically. Create a small custom file containing your overrides instead.

For a shared source installation, clone DRAM2 and run the checkout directly:

```bash
git clone --branch dev --recurse-submodules https://github.com/BortonWrightonLabs/DRAM.git /shared/software/DRAM
nextflow run /shared/software/DRAM --help
```

Replace `/shared/software/DRAM` with a writable installation path. When using a local checkout, select the branch/tag with Git and replace the remote repository and `-r dev` in subsequent examples with the checkout path.

### 4. Save site configuration and run parameters

Nextflow config files hold executor, runtime, cache, and process-resource settings, and can also hold DRAM parameters in a `params` block. YAML or JSON parameters files hold DRAM parameters only. A reusable setup can have:

| File | Purpose | How to load |
| --- | --- | --- |
| `cluster.config` | SLURM partitions, account, QoS, task resources, runtime caches | `-c cluster.config` |
| `databases.config` | Shared database paths in a `params` block | `-c cluster.config,databases.config` |
| `run.yml` | Inputs, outputs, selected steps and databases | `-params-file run.yml` |

Save a run as `run.yml`, using paths valid on your system:

```yaml
input_fasta: /shared/project/genomes
outdir: /shared/project/dram-results
rename: true
annotate: true
anno_dbs: kofam
qc: true
summarize: true
traits: true
visualize: true
```

Run locally with:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    -profile apptainer -c databases.config -params-file run.yml
```

You can also place overrides in `nextflow.config` in the launch directory for automatic loading, or use `includeConfig` to load other config files. See [custom configuration and parameters files](usage.md#custom-configuration-and-parameters-files) for precedence, JSON examples, and combining files.

### 5. Configure SLURM on an HPC system

The built-in `slurm` profile selects the SLURM executor. Add a custom site config to choose the partition, account, QoS, and submission limits for your allocation. Save this as `cluster.config`, replacing the example values:

```groovy
process {
    queue = 'general'
    clusterOptions = '--account=my_account --qos=normal'
}

executor.queueSize = 16

params {
    max_cpus = 24
    max_memory = '200.GB'
    max_time = '48.h'
}
```

Remove account or QoS flags if your cluster does not require them. Set resource caps to match the selected partition's limits. The caps limit each task's request; they do not reserve resources for the whole workflow or increase task requests.

Launch with a runtime profile, the SLURM profile, your configs, and a parameters file:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    -profile apptainer,slurm \
    -c cluster.config,databases.config -params-file run.yml \
    -work-dir /shared/project/dram-work
```

A custom config can alternatively set `process.executor = 'slurm'` itself, in which case the `slurm` profile is optional. These configs work through the normal Nextflow loading mechanisms, including a launch-directory `nextflow.config`, `-c`, or `includeConfig`.

The launch host and compute nodes must be able to access the work directory, inputs, databases, and required software/container caches. Use durable shared storage for work files and outputs; check scratch cleanup policies before long runs. For shared container caches, create a writable directory and set `apptainer.cacheDir` or `singularity.cacheDir` in your site config, for example:

```groovy
apptainer.cacheDir = '/shared/project/caches/apptainer'
```

Nextflow downloads container images or creates Conda environments as needed and reuses them. Allow access to the required repositories/registries and Nextflow plugins, or arrange pre-staged caches with your administrators. DRAM's task dependencies do not need to be installed individually in your login environment.

Generic SLURM examples are available here:

- [CPU SLURM config](configs/slurm_cpu.config): CPU task submission with placeholder partition, account, and QoS values.
- [CPU/GPU SLURM config](configs/slurm_gpu.config): separate CPU/GPU partitions and QoS, a generic single-GPU request, and example per-task resource caps.

These are templates, not built-in profiles or ready-to-run cluster configurations. Replace `cpu_partition`, `gpu_partition`, `my_account`, `cpu_qos`, and `gpu_qos` with values provided by your cluster, or remove flags your site does not require. Adjust resource caps and GPU allocation syntax for your allocation, and set database and cache paths separately. See [running on SLURM](usage.md#running-on-slurm) for commands using these files and GPU requirements.

## Verify the setup

Check that the selected configs merge as expected, without submitting analysis tasks. Replace `/path/to/DRAM` with your checkout or cached pipeline directory containing the revision you pulled (normally `$HOME/.nextflow/assets/BortonWrightonLabs/DRAM`):

```bash
nextflow -c cluster.config,databases.config config /path/to/DRAM \
    -profile apptainer,slurm -flat
```

Then verify that DRAM can display its help:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    -profile apptainer,slurm -c cluster.config,databases.config --help
```

Config inspection and help do not test database contents, compute-node access, or scheduler submission. Verify those with a small run using your own input and one configured database before scaling up. See [usage](usage.md) for resource overrides, batching, arrays, and resuming a run.
