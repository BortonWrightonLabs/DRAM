# DRAM Usage

Here you will find give you basic instructions for running DRAM2
> _The entire list of pipeline configuration parameters can be found here: [Parameters API](params_doc.md). Here we will give some overviews on how to use important parameters and launch DRAM_

## Basic command

Below is an example of common workflow in DRAM2. The user is calling genes from a directory of MAGs, annotating those genes using all available databases, assessing the qualtiy of each MAG. The user is then summarizing their annotations into user-friendly documents, assigning MAG-level metabolic functions, and generating an interactive heatmap of these functions per MAG. This command in being run from the command line in the background. A more detailed description of flags can be found below

`nextflow run BortonWrightonLabs/DRAM --input_fasta [INPUT_FASTA] --outdir [OUTPUT_DIR] --rename --annotate
--anno_dbs all --qc --summarize --traits --visualize -profile singularity -bg` 

## Description of command-line options:

```{note}
All command line options can also be set inside a configuration or params file for set it and forget style parameters instead of needing to be provided each time on the command line. See Nextflow or nf-core documentation for examples.
```

The general command to run DRAM2 is:

`nextflow run BortonWrightonLabs/DRAM [OPTIONS]`

If DRAM2 is installed in a shared location, then the command is:

`nextflow run /path/to/DRAM [OPTIONS]`

If installed in a shared location, replace all example commaands below with `nextflow run /path/to/DRAM [OPTIONS]`

### Launching, Direct or Background

You can launch a Nextflow pipeline, such as DRAM2, directly from the command line. This will output all process information to the current terminal window. If the user is ssh'ed into an HPC and they log out, the run will stop. This can be a fine option if the user is running DRAM2 on a local machine, they launch DRAM2 from a slurm job, or they launch the run in a terminal multiplexer such as `tmux` or `zellij`.

Because the Nextflow scheduler itself takes of very minimal resources, you do not need to launch it from a slurm job, you can launch it in what is called "Background" mode with the `-bg` option. This will allow the user to log out of an ssh session and the DRAM2 run will continue. It will start a process with pid that can be found in a file called `.nextflow.pid` in the launch directory, and if you would like to kill the process you can do so with the command:

`kill "$(cat .nextflow.pid)"`

If you would like to launch DRAM2 in a slurm job, because Nextflow uses very minimal resources, it is suggested to launch it in a small job, such as 1 CPU and 1 GB of RAM. But this job will need to stay alive for the entire duration of the DRAM2 run.

### Important Command-Line Options Explained

`--input_fasta`

This is the location to the input FASTA files. Can be named as such: `*.f*`. File format can be changed with `--fasta_fmt` argument. See [Parameters API](params_doc.md) for more information.

`--outdir`

This is the desired output directory.

`--input_genes`

If the user has already called genes they may use this option to specify the location of a directory containing `*.faa` files. It is key, and is stated in the GitHub documentation, they these files have headers which are unique to a given sample for correct downstream processes. File format can be changed with `--genes_fmt` argument. See [Parameters API](params_doc.md) for more information.


`--annotations`

If the user already has a DRAM2 annotations TSV file, in the correct format, they can provide these using this command-line option.

### Running on Slurm

Use the built-in `slurm` profile to select the Slurm executor. The profile intentionally does not choose a partition, account, QoS, node, or GPU configuration because those settings are specific to each cluster.

Create a site-specific configuration such as `cluster.config`:

```groovy
process {
    queue = 'general'
    clusterOptions = '--account=my_account --qos=normal'
}

executor.queueSize = 100
```

Then compose it with a software profile and the Slurm profile:

```bash
nextflow run WrightonLabCSU/DRAM \
    -profile apptainer,slurm \
    -c cluster.config \
    [OPTIONS]
```

Site configuration files can also use `withLabel` or `withName` selectors to choose different partitions, nodes, or GPU flags for particular tasks. Search processes now live inside a workflow per database. For example, all KEGG MMseqs size buckets can be selected with:

```groovy
process {
    withName: '.*:MMSEQS_KEGG:SEARCH_.*' {
        queue = 'large_memory'
        clusterOptions = '--account=my_account --qos=normal'
    }
}
```

Use `.*:HMM_KOFAM:SEARCH_.*` for KOfam HMM searches, or replace `SEARCH_.*` with `SEARCH_LARGE` for just the large class. Migrate old `MMSEQS_SEARCH_KEGG_.*` / `HMM_SEARCH_KOFAM_.*` selectors to these workflow-qualified selectors. Generic `withName: MMSEQS_SEARCH` / `withName: HMM_SEARCH` selectors and the semantic resource labels still apply. A more specific `clusterOptions` value replaces the inherited value; repeat any required account or QoS settings.

### Resource caps and job arrays

DRAM chooses per-task CPU, memory, and time requests from fixed defaults. CALL_GENES, TRNA_SCAN, RRNA_SCAN, HMM_SEARCH, MMSEQS_SEARCH, and QUAST vary their requests according to input size. Mixed runs are separated into small (at most 1 GiB), medium (over 1 through 20 GiB), and large (over 20 GiB) task classes.

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

### Optional gene-calling and RNA batching

`--call_batch_size 10` runs Prodigal sequentially for up to ten input FASTAs in one CALL_GENES task. `--rna_batch_size 10` similarly groups up to ten FASTAs per task, but tRNAscan-SE and Barrnap still run in separate tasks. Both parameters default to `1`, which preserves one task per input and streams inputs as they become ready.

`--call_batch_max_size '1.GB'` and `--rna_batch_max_size '1.GB'` set the largest individual FASTA allowed to join the corresponding batch. An input above its limit runs alone. Inputs at or below the limit may be grouped up to the configured batch size even when their combined size exceeds the limit. A batch's resource class is the class of its largest member.

When either batch size is greater than one, that stage waits for all its inputs and sorts them by sample name to produce deterministic batches. Wall time is multiplied by the configured batch capacity and then limited by `max_time`; CPU and memory are not multiplied. Outputs are restored to the existing per-sample channels and filenames.

### Optional search batching

`--search_batch_size 10` runs up to ten HMM or MMseqs searches sequentially against one database in a single task. The default, `1`, runs one search per input per database and streams inputs as they become ready. Each search retains its own query, search statistics, gene locations, and output filenames. Queries are not concatenated and searches do not run concurrently inside a batch.

`--search_batch_max_size '1.GB'` (the default) is the largest individual query input allowed to join a batch. Inputs at or below the limit can be grouped up to `search_batch_size`, regardless of their combined size. An input above the limit runs alone. Database size is never considered. For an MMseqs query made of several files, those files together constitute one input. These options affect HMM and MMseqs searches only.

When batching is enabled, each database workflow waits for its input channel to finish and sorts by sample name before packing. This makes batch membership independent of task completion order, at the cost of delaying searches until all queries are ready. A batch's resource class comes from its largest individual protein query, whose size was measured once before database fan-out. The combined size of the batch, database size, and generated MMseqs index size do not affect its class.

CPU and memory follow the class defaults above. Search wall time is multiplied by the configured `search_batch_size`, then capped by `max_time`. Even partial batches use that same multiplier so every array-capable process has uniform initial requests. Choose a smaller batch size or override the search resource labels if the resulting time cap is insufficient. Site overrides must also keep initial scheduler directives uniform within each array-capable process.

Batching and arrays can be used independently or together:

```bash
nextflow run WrightonLabCSU/DRAM \
    -profile apptainer,slurm -c cluster.config \
    --search_batch_size 10 --search_batch_max_size '1.GB' \
    --job_array_size 100 [OPTIONS]
```

Here each array contains up to 100 tasks, and each task searches up to ten inputs. Arrays still contain independently scheduled tasks; batching reduces the number of tasks themselves.

For every batching option, Nextflow caches and retries an entire batch task. A failed member fails the task, and retrying it repeats the other members too; retries occur only when the configured error strategy permits them. Changing the input set or batching parameters can change membership and reduce cache reuse. Per-sample output channels and published filenames are preserved. Start with small batches and increase them only when scheduler overhead is a demonstrated problem.

### Important Core Nextflow Options

Nextflow provides many command-line options to control how the pipeline is run. Below are some of the most important ones for DRAM2 users. You will also notice that all Nextflow options can be seen by running:

`nextflow run -help`

It is also worth noting that all Nextflow options are specified with a single dash `-`, while all DRAM2-specific options are specified with a double dash `--`.

`-bg`

While the user will still see things being output to the current screen, the user can log out and the DRAM2 run will continue.

`-profile`

This is the Nextflow profile to use. The profile determines how software dependencies are handled and what compute environment settings are used. Common profiles include `singularity`, `apptainer`, `docker`, `conda`, and `slurm`. Profiles can be composed as a comma-separated list.

Additionally, short hand modes exist for common run modes, such as `full_mode`, which will run the entire pipeline (without rename), and with `--anno_dbs all`. See the nextflow.config file on GitHub for the full list of profiles.

`-resume`

If the user has already run this command, or a version of it, Nextflow will look for a `work/` directory, in the current directory, to reuse previous analyses/data. If the user changes command-line options, the pipeline will attempt to resume where these changes were made.

`-with-trace`

This option is a Nextflow-provided option which produces a continuously updated log of DRAM2 processes. This is a good place to check how a run is proceeding and is anything has failed.


#### Pipeline Steps

`--rename`

Rename the headers of the input FASTA files such that they will have a unique prefix based on the FASTA file name. This is optional.

`--annotate`

Annotate called genes. You will need to specify what databases to annotate against with `--anno_dbs [OPTIONS]` or `--use_[DB]`. See the Parameters API documentation for more details, or `--help`.

`--qc`

Run quality control options for the DRAM workflow. With `--input_fasta`, QC scans for rRNA and tRNA using Barrnap and tRNAscan-SE. Without raw FASTA, QC can collect precomputed `--rrnas` and `--trnas` tables. It can also add `--bin_quality` and `--taxa` data to annotations produced by `--annotate` or supplied with `--annotations`. QC outputs remain under the `ANNOTATE` output directory.

`--summarize`

Distill out annotations from the topic toolkit default (set of predetermined distill topics). You can also specify additional ecosystem toolkits with `--sum_ecos [OPTIONS]` or custom distill sheets. To summarize without running `--annotate`, provide an existing DRAM annotations TSV with `--annotations`. QC remains optional in either mode. See the Parameters API documentation for more details, or `--help`.

`--visualize`

Create visualizations from the distilled annotations.

`--traits`

Distill out traits from the annotated genes.

### Other Command-Line Options Notes

Other command-line options exist to control specific parameters of the DRAM2 pipeline. These are all described in the [Parameters API](params_doc.md) documentation page, or can be seen by running:

`nextflow run BortonWrightonLabs/DRAM --help`

---

## DRAM2 example commands

Simple run with rename, annotate, QC, summarize, and visualize:

```
nextflow run BortonWrightonLabs/DRAM --input_fasta [INPUT_FASTA] --outdir [OUTPUT_DIR] --rename --annotate
--anno_dbs camper,kegg --qc --summarize --visualize -profile singularity
```

Add resume option and ecosystem summaries:

```
nextflow run BortonWrightonLabs/DRAM --input_fasta [INPUT_FASTA] --outdir [OUTPUT_DIR] --rename --annotate
--anno_dbs camper,kegg --qc --summarize --sum_ecos 'eng_sys,ag' --visualize -profile singularity -resume
```

Run all standard databases and launch on slurm and background:

```
nextflow run BortonWrightonLabs/DRAM --input_fasta [INPUT_FASTA] --outdir [OUTPUT_DIR] --rename --annotate
--anno_dbs all --qc --summarize --sum_ecos 'eng_sys,ag' --visualize -profile apptainer,slurm -c cluster.config -resume -bg
```

The same as the above command but with full_mode to simplify the command:

```
nextflow run BortonWrightonLabs/DRAM --input_fasta [INPUT_FASTA] --outdir [OUTPUT_DIR] --rename --sum_ecos 'eng_sys,ag' -profile apptainer,slurm,full_mode -c cluster.config -resume -bg
```

Utilizing a custom nextflow.config file to pass specific parameters (with a custom configuration file, DRAM parameters can be set there and do not need to be specified on the command-line, but Nextflow options still do):

```
nextflow run BortonWrightonLabs/DRAM -c [PATH/TO/NEXTFLOW.CONFIG] -profile singularity -resume -bg
```
