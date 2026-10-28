# DRAM Usage

DRAM2 accepts assemblies, predicted protein FASTAs, or existing DRAM annotations, depending on the selected steps. See the [installation guide](installation.md) for software, databases, and initial HPC setup, and the [Parameters API](params_doc.md) for all DRAM parameters.

## Basic command

This example calls genes from assemblies, annotates against KOfam, runs QC, and produces summaries, traits, and visualizations:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    --input_fasta /shared/project/genomes --outdir /shared/project/dram-results \
    --rename --annotate --anno_dbs kofam --qc --summarize --traits --visualize \
    -profile apptainer -c databases.config
```

Set the KOfam paths in `databases.config` as described in [installation](installation.md#2-prepare-a-launch-directory-and-databases). `--anno_dbs all` enables databases with existing configured paths and warns and skips missing paths; an incomplete existing database can still fail later. Explicitly name databases to keep the annotation set predictable. Annotation from `--input_fasta` automatically calls genes; `--call` is useful when requesting gene calling on its own.

Examples use `-r dev` for DRAM2. Replace it with a DRAM2 tag or commit for a reproducible run. For a local or shared checkout, replace `BortonWrightonLabs/DRAM -r dev` with `/path/to/DRAM` and select the revision with Git.

## Custom configuration and parameters files

Nextflow options use a single dash, such as `-profile`, `-c`, `-params-file`, and `-resume`. DRAM parameters use a double dash, such as `--input_fasta` and `--max_memory`.

| Setting | Nextflow config (`.config`) | Parameters file (`.yml` / `.json`) | Command line |
| --- | --- | --- | --- |
| Input directory | `params.input_fasta = '/data/genomes'` | `input_fasta: /data/genomes` | `--input_fasta /data/genomes` |
| Per-task memory cap | `params.max_memory = '80.GB'` | `max_memory: '80.GB'` | `--max_memory '80.GB'` |
| SLURM partition | `process.queue = 'general'` | Set in a config | Load config with `-c` |
| Process resource overrides | `process { withLabel: ... }` | Set in a config | Load config with `-c` |
| Runtime and workflow profiles | Define under `profiles` | Select on the command line | `-profile apptainer,slurm` |

### Loading custom configs

A custom config adds to the pipeline configuration. Save only your overrides; the pipeline's own config and its includes are loaded automatically.

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    -profile apptainer,slurm -c /shared/configs/cluster.config \
    -params-file run.yml
```

Normal Nextflow loading mechanisms all apply:

- Save a file named `nextflow.config` in the launch directory for automatic loading. This is the directory where you issue the command, which may differ from the pipeline checkout.
- Use `-c /path/to/custom.config` to add an explicitly named file, or `-c cluster.config,databases.config,resources.config` to combine files. Later files override earlier assignments to the same setting, subject to process-selector priority.
- Use `includeConfig '/shared/configs/cluster.config'` in another config. Relative include paths are resolved relative to the file containing the include.
- Use `$NXF_HOME/config` (normally `$HOME/.nextflow/config`) for user-wide defaults affecting all pipelines.

For assignments to the same config setting, precedence increases from user-wide config, to project config, to launch-directory config, to files passed with `-c`. Use lowercase `-c` for routine overrides. Uppercase `-C` ignores the normal config files, including DRAM's defaults and includes, so it is unsuitable for a small override file. See the [Nextflow configuration guide](https://www.nextflow.io/docs/stable/config.html#configuration-files).

### YAML and JSON parameters files

Save DRAM parameters as a top-level mapping without `params`, `--` prefixes, or Nextflow options. For example, `run.yml`:

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
max_cpus: 12
max_memory: '80.GB'
max_time: '24.h'
```

The equivalent JSON file, `run.json`, is:

```json
{
  "input_fasta": "/shared/project/genomes",
  "outdir": "/shared/project/dram-results",
  "rename": true,
  "annotate": true,
  "anno_dbs": "kofam",
  "qc": true,
  "summarize": true,
  "traits": true,
  "visualize": true,
  "max_cpus": 12,
  "max_memory": "80.GB",
  "max_time": "24.h"
}
```

Load either file with `-params-file run.yml` or `-params-file run.json`. YAML/JSON files contain literal values: Groovy expressions such as `80.GB` and `${launchDir}` are not evaluated there. Use quoted unit strings such as `'80.GB'` and absolute paths for files shared between projects. Relative input/output paths are interpreted from the launch directory, not from the parameters file's location. Comma-separated DRAM options such as `anno_dbs` should remain strings, for example `anno_dbs: 'kofam,camper'`.

DRAM parameter precedence is config defaults/overrides, then `-params-file`, then explicit `--parameter value` arguments. For example, this uses the settings in `run.yml` but writes to a different output directory:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    -profile apptainer,slurm -c cluster.config,databases.config \
    -params-file run.yml --outdir /shared/project/second-results
```

Keep `-profile`, `-c`, `-params-file`, `-work-dir`, and `-resume` on the command line. Parameters files are not loaded automatically. See the [Nextflow CLI guide](https://www.nextflow.io/docs/stable/cli.html#pipeline-parameters) for parameter-file behavior.

## Launching directly or in the background

The Nextflow driver must remain running while it submits and monitors tasks. Follow your cluster's policy: run it in a persistent terminal such as `tmux`, on an approved workflow host, or inside a SLURM driver job. A driver job must stay alive for the entire analysis and must be able to submit further jobs. Its resource allocation is separate from the CPU, memory, and time requested for DRAM tasks; size it for the workflow and your site's guidance rather than assuming a fixed 1 GB is sufficient.

`-bg` runs the Nextflow driver in the background and records output in the Nextflow log. It does not submit the driver to SLURM or bypass login-node policies and session cleanup. When running the driver inside a batch script, keep Nextflow in the foreground so the driver job waits for it to finish.

## Important Command-Line Options Explained

`--input_fasta`

Directory containing assembly FASTAs. The default filename pattern is `*.f*`; change it with `--fasta_fmt`, quoting wildcard patterns on the command line. See [Parameters API](params_doc.md) for more information.

`--outdir`

This is the desired output directory.

`--input_genes`

Directory containing predicted protein FASTAs (`*.faa` by default). Gene identifiers must be unique across samples for downstream processing; use `--rename` if needed. Change the filename pattern with `--genes_fmt`. Supply matching nucleotide gene FASTAs when required by selected annotation tools; see `genes_fna_fmt` in the Parameters API. See [Parameters API](params_doc.md) for more information.


`--annotations`

If the user already has a DRAM2 annotations TSV file, in the correct format, they can provide these using this command-line option.

## Running on SLURM

Use `-profile apptainer,slurm` or `-profile singularity,slurm` and a site config defining the partition, account/QoS, and submission limits. The built-in `slurm` profile selects only the executor. Without it or an equivalent `process.executor = 'slurm'` setting, tasks use the local executor. A SLURM allocation for the driver alone does not configure task submission.

See [SLURM setup](installation.md#5-configure-slurm-on-an-hpc-system) for a minimal `cluster.config` and shared-storage requirements. Use `process.queue` for the partition and `process.clusterOptions` for extra options such as account, QoS, node constraints, or GPU allocation. Set CPUs, memory, and time with Nextflow directives, rather than duplicating them with `--cpus-per-task`, `--mem`, or `--time` in `clusterOptions`. For clusters requiring memory per CPU, Nextflow supports `executor.perCpuMemAllocation = true`. See the [Nextflow SLURM reference](https://docs.seqera.io/nextflow/reference/executor/slurm).

The [CPU example](configs/slurm_cpu.config) and [CPU/GPU example](configs/slurm_gpu.config) use placeholder partition, account, and QoS values. Save copies alongside your run files and replace those values for your allocation. Both set the executor directly and can be loaded by `-c`, `includeConfig`, or as a launch-directory `nextflow.config`; their filenames have no special meaning to Nextflow.

CPU tasks using Singularity and separately configured database paths:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    -profile singularity -c slurm_cpu.config,databases.config \
    -params-file run.yml -work-dir /shared/project/dram-work
```

CPU and GPU tasks using Apptainer:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    -profile apptainer,gpu -c slurm_gpu.config,databases.config \
    -params-file run.yml -work-dir /shared/project/dram-work
```

The CPU/GPU example routes `process_gpu` tasks to `gpu_partition` with a single-GPU request; ordinary tasks use `cpu_partition`. Replace both partition names, account and QoS placeholders, and GPU allocation syntax with settings accepted by your cluster. The built-in `gpu` profile selects GPU MMseqs searches and exposes GPUs to containers. Requesting a GPU in SLURM alone does not select the GPU search implementation. GPU runs also require suitable NVIDIA nodes/drivers and GPU-formatted database paths such as `kegg_gpu_db`; a CPU-formatted MMseqs database is not interchangeable. `--mmseqs_gpu_exclude_dbs` keeps selected databases on the CPU route. Large GPU database indexes may require increasing both the process memory request and `max_memory` beyond the template's example cap.

Configure database paths in `databases.config` and choose a runtime with `-profile`. Set partitions with `process.queue`, submission limits with `executor.queueSize`, and account/QoS/GPU flags with `clusterOptions`. A selector's `clusterOptions` value replaces the inherited string, so repeat any required account flag in both CPU and GPU settings.

`executor.queueSize` limits the executor's submitted task queue; `executor.submitRateLimit` throttles submissions. A process-specific `maxForks` limits concurrent tasks for that process. These settings are distinct from per-task resource caps, batching, and arrays.

## Resource caps and job arrays

DRAM chooses first-attempt, unbatched CPU, memory, and time requests from the defaults below, subject to resource caps and overrides. CALL_GENES, TRNA_SCAN, RRNA_SCAN, HMM_SEARCH, MMSEQS_SEARCH, and QUAST vary their requests according to input size. Mixed runs are separated into small (at most 200 MiB), medium (over 200 MiB through 1 GiB), and large (over 1 GiB) task classes.

Set `--resource_class_small_max_size '200.MB'` and `--resource_class_medium_max_size '1.GB'` to change the inclusive upper limits of the small and medium classes. Larger inputs use the large class. Both limits must be positive, and the medium limit must exceed the small limit. Nextflow size units are binary: `200.MB` means 200 MiB.

Class thresholds control which resource requests an input receives. The independent `*_batch_size` and `*_batch_max_size` parameters control how many inputs share a task and which inputs may join a batch. To change CPU, memory, or time requests within a class, override the resource labels from `conf/base.config` in your custom config.

Workload size is stored as per-sample channel metadata rather than re-read by every downstream database. DRAM measures the final decompressed/renamed input FASTA once for CALL_GENES, TRNA_SCAN, and RRNA_SCAN. After gene calling, it separately measures the called protein FASTA for every HMM/MMseqs search and the filtered FASTA for consumers such as QUAST and antiSMASH. Files, collections, and directory contents within one input are summed recursively. Database size, auxiliary description files, metadata tables, and the physical size of a generated MMseqs index are not included.

| Processes | Small | Medium | Large |
| --- | --- | --- | --- |
| CALL_GENES, TRNA_SCAN, RRNA_SCAN, and QUAST | 4 CPUs, 12 GB, 4 hours | 6 CPUs, 36 GB, 8 hours | 24 CPUs, 200 GB, 168 hours |
| HMM_SEARCH and MMSEQS_SEARCH | 6 CPUs, 36 GB, 8 hours | 12 CPUs, 72 GB, 16 hours | 24 CPUs, 200 GB, 168 hours |

The following parameters cap a single task's request:

- `--max_cpus 24`
- `--max_memory '200.GB'`
- `--max_time '168.h'`

These are upper limits only; raising them does not increase a process request. A cluster configuration can override label resources when larger or smaller defaults are required.

Set `--job_array_size` to enable job arrays for bucketed CALL_GENES, TRNA_SCAN, RRNA_SCAN, HMM_SEARCH, and MMSEQS_SEARCH tasks on an executor that supports arrays. Values `0` and `1` disable arrays; values of `2` or greater specify the maximum number of tasks per array. Do not enable this parameter with an unsupported executor. Gene calling, tRNA scanning, and rRNA scanning remain separate process families, so each can fail, retry, and receive site-specific overrides independently.

## Overriding labels and process resources

Resource labels group tasks under the policies in `conf/base.config`. Override their directives in a custom config rather than editing the pipeline or renaming labels. The input-sensitive labels are:

| Label | Processes affected |
| --- | --- |
| `process_call_genes` | Prodigal gene calling |
| `process_trna_scan` | tRNAscan-SE |
| `process_rrna_scan` | Barrnap |
| `process_quast` | QUAST |
| `process_hmm_search` | All HMM searches |
| `process_mmseqs_search` | CPU and GPU MMseqs searches |
| `process_gpu` | GPU tasks; also configures GPU/container access |
| `process_array` | Tasks eligible for `job_array_size` |

Generic labels provide fixed first-attempt defaults for other processes:

| Label | CPUs | Memory | Time |
| --- | --- | --- | --- |
| `process_tiny` | 1 | 1 GB | 1 hour |
| `process_single` | 1 | 12 GB | 4 hours |
| `process_small` | 4 | 12 GB | 4 hours |
| `process_medium` | 6 | 36 GB | 8 hours |
| `process_big` | 12 | 72 GB | 16 hours |
| `process_huge` | 24 | 200 GB | 168 hours |

The semantic search labels apply to searches in every size class. Overriding `process_medium` does not change a search's medium class; override `process_hmm_search` or `process_mmseqs_search` instead.

For example, save this as `resources.config` to set fixed requests for all MMseqs searches and larger requests for the large KEGG CPU search class:

```groovy
params {
    max_cpus = 32
    max_memory = '256.GB'
    max_time = '72.h'
}

process {
    withLabel: 'process_mmseqs_search' {
        cpus = 8
        memory = '64.GB'
        time = '12.h'
    }

    withName: '.*:MMSEQS_KEGG:SEARCH_LARGE' {
        cpus = 32
        memory = '256.GB'
        time = '48.h'
        queue = 'large_memory'
    }
}
```

Load it after your site settings with `-c cluster.config,databases.config,resources.config`. Check that your parameters file or explicit `--max_*` arguments do not lower these caps. `max_memory`, `max_cpus`, and `max_time` cap each task; they do not limit total workflow usage. `--threads` is not a replacement for process CPU directives.

To retain size-based CPU/memory requests while changing only search wall time, use a dynamic directive:

```groovy
process {
    withLabel: 'process_mmseqs_search' {
        time = { (resource_class == 'small' ? 12.h : resource_class == 'medium' ? 24.h : 48.h) * params.search_batch_size * task.attempt }
    }
}
```

Fixed overrides replace the default expressions, including their retry scaling and batching multipliers. The dynamic example preserves both for wall time. Defaults generally scale resources with `task.attempt` on retries, subject to the same caps; retries occur only when the error strategy allows them. Set requests to values supported by the chosen partition.

For selector priority, `withName` overrides `withLabel`, which overrides unselected `process` defaults. An included process alias takes priority over its original name, and a fully qualified selector takes priority over either. A plain `process.memory` override therefore may not affect labeled DRAM tasks. See [Nextflow process selectors](https://www.nextflow.io/docs/stable/config.html#process-selectors).

Searches run inside a workflow per database. Useful selectors include:

| Selector | Scope |
| --- | --- |
| `withName: MMSEQS_SEARCH` | All CPU MMseqs searches |
| `withName: MMSEQS_SEARCH_GPU` | All GPU MMseqs searches |
| `withName: HMM_SEARCH` | All HMM searches |
| `withName: '.*:MMSEQS_KEGG:SEARCH_.*'` | All KEGG CPU size classes |
| `withName: '.*:HMM_KOFAM:SEARCH_LARGE'` | Large KOfam HMM tasks |
| `withName: '.*:MMSEQS_GPU_KEGG:SEARCH_GPU_.*'` | All KEGG GPU size classes |

Replace old `MMSEQS_SEARCH_KEGG_.*` / `HMM_SEARCH_KOFAM_.*` selectors with these workflow-qualified patterns. Use the task names in `.nextflow.log` or the execution trace to identify the database workflow and process alias. Keep initial scheduler directives uniform within each array-capable process when using job arrays.

Inspect merged config before launching, using your local checkout or the cached pipeline directory containing the revision you pulled:

```bash
nextflow -c cluster.config,databases.config,resources.config config /path/to/DRAM \
    -profile apptainer,slurm -flat
```

This checks config loading but does not validate every selector against running tasks or apply a run's `-params-file`. Check actual CPU/memory/time requests in the execution trace and the task's `work/.../.command.run` submission script after a small run.

## Optional gene-calling and RNA batching

`--call_batch_size 10` runs Prodigal sequentially for up to ten input FASTAs in one CALL_GENES task. `--rna_batch_size 10` similarly groups up to ten FASTAs per task, but tRNAscan-SE and Barrnap still run in separate tasks. Both parameters default to `1`, which preserves one task per input and streams inputs as they become ready.

`--call_batch_max_size '1.GB'` and `--rna_batch_max_size '1.GB'` set the largest individual FASTA allowed to join the corresponding batch. An input above its limit runs alone. Inputs at or below the limit may be grouped up to the configured batch size even when their combined size exceeds the limit. A batch's resource class is the class of its largest member.

When either batch size is greater than one, that stage waits for all its inputs and sorts them by sample name to produce deterministic batches. Wall time is multiplied by the configured batch capacity and then limited by `max_time`; CPU and memory are not multiplied. Outputs are restored to the existing per-sample channels and filenames.

## Optional search batching

`--search_batch_size 10` runs up to ten HMM or MMseqs searches sequentially against one database in a single task. The default, `1`, runs one search per input per database and streams inputs as they become ready. Each search retains its own query, search statistics, gene locations, and output filenames. Queries are not concatenated and searches do not run concurrently inside a batch.

`--search_batch_max_size '1.GB'` (the default) is the largest individual query input allowed to join a batch. Inputs at or below the limit can be grouped up to `search_batch_size`, regardless of their combined size. An input above the limit runs alone. Database size is never considered. For an MMseqs query made of several files, those files together constitute one input. These options affect HMM and MMseqs searches only.

When batching is enabled, each database workflow waits for its input channel to finish and sorts by sample name before packing. This makes batch membership independent of task completion order, at the cost of delaying searches until all queries are ready. A batch's resource class comes from its largest individual protein query, whose size was measured once before database fan-out. The combined size of the batch, database size, and generated MMseqs index size do not affect its class.

CPU and memory follow the class defaults above. Search wall time is multiplied by the configured `search_batch_size`, then capped by `max_time`. Even partial batches use that same multiplier so every array-capable process has uniform initial requests. Choose a smaller batch size or override the search resource labels if the resulting time cap is insufficient. Site overrides must also keep initial scheduler directives uniform within each array-capable process.

Batching and arrays can be used independently or together:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    -profile apptainer,slurm -c cluster.config \
    --search_batch_size 10 --search_batch_max_size '1.GB' \
    --job_array_size 100 [OPTIONS]
```

Here each array contains up to 100 tasks, and each task searches up to ten inputs. Arrays still contain independently scheduled tasks; batching reduces the number of tasks themselves.

For every batching option, Nextflow caches and retries an entire batch task. A failed member fails the task, and retrying it repeats the other members too; retries occur only when the configured error strategy permits them. Changing the input set or batching parameters can change membership and reduce cache reuse. Per-sample output channels and published filenames are preserved. Start with small batches and increase them only when scheduler overhead is a demonstrated problem.

## Important Core Nextflow Options

Nextflow provides many command-line options to control how the pipeline is run. Below are some of the most important ones for DRAM2 users. You will also notice that all Nextflow options can be seen by running:

`nextflow run -help`

It is also worth noting that all Nextflow options are specified with a single dash `-`, while all DRAM2-specific options are specified with a double dash `--`.

`-bg`

Run the Nextflow driver in the background. Use it only where cluster policy permits persistent background processes; see [launching directly or in the background](#launching-directly-or-in-the-background).

`-profile`

This is the Nextflow profile to use. The profile determines how software dependencies are handled and what compute environment settings are used. Common profiles include `singularity`, `apptainer`, `docker`, `conda`, and `slurm`. Profiles can be composed as a comma-separated list.

The `full_mode` profile enables annotate, QC, summarize, traits, visualize, and `anno_dbs = 'all'`. It does not enable rename. Runtime and executor profiles can be combined with it; choose one runtime. See `nextflow.config` for all built-in profiles. With the default config parser, profiles are applied in their definition order, not their order in the comma-separated list.

`-resume`

Reuse successfully completed tasks whose inputs, scripts, and relevant settings still match. Preserve both the launch directory's `.nextflow/cache` and the work directory selected with `-work-dir` (default `work/`). Resume from the same launch directory, using the same work directory and pipeline revision where possible. `-resume` resumes the latest run; `-resume <run_name_or_session_id>` selects a specific run. Changed inputs or settings can cause tasks to rerun; output files alone are insufficient to resume.

`-with-trace`

Write task execution details. DRAM already enables trace, report, timeline, and DAG outputs under `<outdir>/pipeline_info/`. Use `.nextflow.log` in the launch directory for driver and submission errors, and task `.command.err`, `.command.out`, and `.command.run` files in the work directory for task failures.


## Pipeline steps

`--rename`

Prefix assembly or protein FASTA headers with the sample filename to make identifiers unique across samples. This is optional.

`--call`

Call genes with Prodigal without requiring annotation. Gene calling is also enabled automatically when `--annotate` is combined with `--input_fasta`.

`--annotate`

Annotate called genes. You will need to specify what databases to annotate against with `--anno_dbs [OPTIONS]` or `--use_[DB]`. See the Parameters API documentation for more details, or `--help`.

`--qc`

Run quality control options for the DRAM workflow. With `--input_fasta`, QC scans for rRNA and tRNA using Barrnap and tRNAscan-SE. Without raw FASTA, QC can collect precomputed `--rrnas` and `--trnas` tables. It can also add `--bin_quality` and `--taxa` data to annotations produced by `--annotate` or supplied with `--annotations`. QC outputs remain under the `ANNOTATE` output directory.

`--summarize`

Distill out annotations from the topic toolkit default (set of predetermined distill topics). You can also specify additional ecosystem toolkits with `--sum_ecos [OPTIONS]` or custom distill sheets. To summarize without running `--annotate`, provide an existing DRAM annotations TSV with `--annotations`. QC remains optional in either mode. See the Parameters API documentation for more details, or `--help`.

`--visualize`

Create interactive metabolic heatmaps from annotations produced in this run or supplied with `--annotations`.

`--traits`

Evaluate trait rules against gene annotations and write `df_traits.tsv` and `heatmap_traits.html` under `VISUALIZE/`.

## Other Command-Line Options Notes

Other command-line options exist to control specific parameters of the DRAM2 pipeline. These are all described in the [Parameters API](params_doc.md) documentation page, or can be seen by running:

`nextflow run BortonWrightonLabs/DRAM -r dev --help`

---

## DRAM2 example commands

Annotate pre-called proteins with KOfam:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    --input_genes /shared/project/proteins --outdir /shared/project/protein-results \
    --rename --annotate --anno_dbs kofam \
    -profile apptainer -c databases.config
```

Summarize existing DRAM annotations without rerunning annotation:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    --annotations /shared/project/annotations.tsv --outdir /shared/project/summary-results \
    --summarize --traits --visualize --sum_ecos 'eng_sys,ag' \
    -profile apptainer
```

Run all databases found at their configured paths on SLURM, including traits, and reuse eligible completed tasks:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    --input_fasta /shared/project/genomes --outdir /shared/project/dram-results \
    --rename --annotate --anno_dbs all --qc --summarize --traits --visualize \
    --sum_ecos 'eng_sys,ag' \
    -profile apptainer,slurm -c cluster.config,databases.config \
    -work-dir /shared/project/dram-work -resume
```

The same steps through `full_mode`:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    --input_fasta /shared/project/genomes --outdir /shared/project/dram-results \
    --rename --sum_ecos 'eng_sys,ag' \
    -profile apptainer,slurm,full_mode -c cluster.config,databases.config \
    -work-dir /shared/project/dram-work -resume
```

Reuse saved run parameters and override resources:

```bash
nextflow run BortonWrightonLabs/DRAM -r dev \
    -profile apptainer,slurm \
    -c cluster.config,databases.config,resources.config -params-file run.yml \
    -work-dir /shared/project/dram-work -resume
```
