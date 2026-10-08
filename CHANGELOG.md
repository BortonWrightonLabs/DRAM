# Changelog

All notable changes to this project will be documented in this file.

## 2.0.0-beta38 - 2026-10-03

[4594735](https://github.com/BortonWrightonLabs/DRAM/commit/45947355343e5e9261fd23c59e68c03434a49ece)...[59af0df](https://github.com/BortonWrightonLabs/DRAM/commit/59af0df029f749f7fb57ce1abb4f84f5537d7ef5)

### Bug Fixes

- Decouple SUMMARIZE from ANNOTATE output through QC for annotations ([bc823d6](https://github.com/BortonWrightonLabs/DRAM/commit/bc823d6b35402dbad41a87d968ad2cbf753ad85b))

  SUMMARIZE was reliant on ANNOTATIONS output directly, through the access
  of ANNOTATE.out.ch_trna_combined (from QC), meaning --annotations
  failed. Now these are decoupled, but QC still outputs to the ANNOTATE
  output namespace.


- No longer gen gff file, fixing dbcan output ([afd40b1](https://github.com/BortonWrightonLabs/DRAM/commit/afd40b1971bc38c5fc135126a2b4d22948c16a97))

  DRAM no longer will try to generate a gff file from called genes. dbcan
  CGC needs a gff file, so called genes can't run CGC anymore, but by
  default we don't need CGC. Add option to save CGC output if users
  want it, but only run CAZyme Annotation normally, and fall back to
  CAZyme Annotation if users input called genes and try to save CGC.

  antiSMASH can also not be ran with called genes anymore because it
  also needs a gff file.



### Features

- Update common rules for traits, ag, and bgc. alias rules syntax ([59af0df](https://github.com/BortonWrightonLabs/DRAM/commit/59af0df029f749f7fb57ce1abb4f84f5537d7ef5))

  Add alias syntax for rules parsing. Must use `@` now for alias.
  Update traits, viz ag, and viz bgc with common rules.
  traits now uses dram_viz directly and outputs df and heatmap

  Add a syntax to specify aliases, an alias is now preceeded with an @ in the rule definition to resolve the alias, ex: @SomeAlias1 | @SomeAlias2 If you don't preface them with an @ they don't resolve. Need to add a check for if you don't include an @. This would look like checking if any NAME/gene_id defined matches an alias. If you use an alias and it isn't defined, then you get a rules error.

  Add rule_options column option for general rule behavior like requiring certain columns in the annotation for a rule to show up at all.


## 2.0.0-beta37 - 2026-09-08

[24582dc](https://github.com/BortonWrightonLabs/DRAM/commit/24582dc53c47024fd654dab5d5933611153ed51d)...[961ddde](https://github.com/BortonWrightonLabs/DRAM/commit/961ddde2fc8f112ea01ea75c408767c2d777af78)

### Bug Fixes

- Hotfix distill_bgc spacing error ([b7d9ddc](https://github.com/BortonWrightonLabs/DRAM/commit/b7d9ddcd420f6882edd0d1d5cec2a3e14de8b186))


- Email flag fix to send emails on run complete ([5024106](https://github.com/BortonWrightonLabs/DRAM/commit/5024106dd8121125a4ea7a8255786c6ae15ef966))

  The email flag was silently failing for a few reasons. Inocrrect paths to assets,
  not passing the header, and not giving feedback on sendmail result.
  The plaintext email also failed because of not sending the header properly.
  Now it tries sendmail for the html email, if that fails, it uses the plaintext email
  as a backup and lets you know this in the console output and in log.



### Documentation

- Update headers and links ([229ada3](https://github.com/BortonWrightonLabs/DRAM/commit/229ada3668abbdaf0d7508b72dbf003dbd4ce3ad))



### Features

- GPU mmseqs support ([2517f88](https://github.com/BortonWrightonLabs/DRAM/commit/2517f8863aa45706a80cdcc0519d3d09cd6303f4))

  Add optional GPU acceleration for MMseqs2 searches through the GPU
  profile, including GPU database preparation, validation, and per-database
  CPU exclusions.

  Integrate CPU and GPU searches with the shared batching workflows,
  size-based resource allocation, and executor job arrays. Update pipeline
  configuration, schema, documentation, and tests.

- Dynamically allocate resources based on size, remove slurm config ([463ebf2](https://github.com/BortonWrightonLabs/DRAM/commit/463ebf27e2d671b3009ee67b3560c305d36ebc4f))

  - Dynamically bucket CALL_GENES, QUAST, HMM_SEARCH, and MMSEQS_SEARCH tasks by input workload size.
  - Add opt-in, resource-uniform job arrays for bucketed CALL_GENES, HMM_SEARCH, and MMSEQS_SEARCH tasks, BREAKING CHANGE:Replace the built-in site-specific Slurm configuration with a minimal `slurm` profile and user-supplied cluster configuration. Replace tier-specific resource parameters with `max_cpus`, `max_memory`, and `max_time` caps, and rename `array_size` to `job_array_size`.


- Add job batching for call, rna, and db scans ([e2be421](https://github.com/BortonWrightonLabs/DRAM/commit/e2be421d327ec50e159ee78f3143e834eb0f9c27))

  Input batching for CALL, rna scan and mmseqs and hmmer search,
  inputs can be batched together with inputs above a certain size
  being ran on their own job. This is allows users to batch inputs
  in situations when a SLURM queue is very full and scheduling
  many small jobs is difficult. In this siutation, it might be
  better to batch them together for when they do get scheduled.



## 2.0.0-beta36 - 2026-08-11

[144002b](https://github.com/WrightonLabCSU/DRAM/commit/144002b7b7938db8c1d51f0559641585fb706376)...[98a3adc](https://github.com/WrightonLabCSU/DRAM/commit/98a3adcc19926e53da38b0831ee14e0a384d7e7a)

### Bug Fixes

- Update diamond to fix hang problem ([1c4a8cf](https://github.com/WrightonLabCSU/DRAM/commit/1c4a8cfcecf9b7268fffe1513819870b872e22ee))

  Update rundbcan easysubstrate and pin diamond to 2.2.5.
  In diamond 2.2.3 they mention fixing a problem with hanging sometimes,
  pinning diamond above that seems to eliminate the occassional dbcan
  hang problem.



### Features

- Update BGC rules ([5f1747b](https://github.com/WrightonLabCSU/DRAM/commit/5f1747b31852e3fd53d1157e0a6b2f4b1190aaa7))



## 2.0.0-beta35 - 2026-08-10

### Features

- Update to BGC Rules [7607d5c](https://github.com/WrightonLabCSU/DRAM/commit/7607d5c6cc79a32a72c4b23625113263c7ede482)...[b440963](https://github.com/WrightonLabCSU/DRAM/commit/b4409636f80734aa159295d7819680c929a115d0)

## 2.0.0-beta34 - 2026-07-31

[4c469d7](https://github.com/WrightonLabCSU/DRAM/commit/4c469d73a9e1f9dc942802e42d14fcc6255c6fd4)...[4c051ec](https://github.com/WrightonLabCSU/DRAM/commit/4c051ecfd70bdf58a274eee68d06052b140c071d)

### Features

- Update trait rules with tax ([3d54a95](https://github.com/WrightonLabCSU/DRAM/commit/3d54a95560f517e7ad9b5f50d979a5c19093bf9d))


- Add gut rules ([4c051ec](https://github.com/WrightonLabCSU/DRAM/commit/4c051ecfd70bdf58a274eee68d06052b140c071d))



## 2.0.0-beta33 - 2026-07-27

[eadadea](https://github.com/WrightonLabCSU/DRAM/commit/eadadeaa4b282e35f1fa779289716e2d188316b5)...[7ae8c45](https://github.com/WrightonLabCSU/DRAM/commit/7ae8c4569b54832fe1585250b3c2ee9b4931ecff)

### Features

- Update and add new ecosystem summaize sheets ([c718b7f](https://github.com/WrightonLabCSU/DRAM/commit/c718b7f4feffe3ce2eccdcab7a4a23a5df54fc4f))

  Update eng_sys sheet
  Add new gut, marine, and biogeochemical sheets


- Add new ecos sheets from viz update ([1ae7ac2](https://github.com/WrightonLabCSU/DRAM/commit/1ae7ac21723468269bc2a23700c188c2b6ed511e))

  Add marine, eng_sys, and bgc to viz sheet options



## 2.0.0-beta32 - 2026-07-16

[42dad45](https://github.com/WrightonLabCSU/DRAM/commit/42dad45e8321853fd58b560966a7481b60725f6c)...[bae4593](https://github.com/WrightonLabCSU/DRAM/commit/bae459344a64b0ad29ad2aac9756dcd8a696bfec)

### Bug Fixes

- Update vix for mapping fixes, and dram cli inputs ([2fc9d76](https://github.com/WrightonLabCSU/DRAM/commit/2fc9d769cd6d1595f2a437a3e024b6ae620bcac8))

  Update DRAM cli inputs for running annotationis stand alone,
  input genes with mapping options, and mapping option overrides

  Update viz package for bug fixes

  Update NF container tags for updated apptainer and singularity versions.
  Adds extra apptainer/singularity URIs for container image resolution.


## 2.0.0-beta31 - 2026-07-09

[c065dce](https://github.com/WrightonLabCSU/DRAM/commit/c065dce9a431c6fda55ab0e4a6b464fdbf0c194c)...[ccb7d35](https://github.com/WrightonLabCSU/DRAM/commit/ccb7d35714fd325767a176a6802c75ada613f092)

### Features

- Update Rules and rule parsing ([ccb7d35](https://github.com/WrightonLabCSU/DRAM/commit/ccb7d35714fd325767a176a6802c75ada613f092))

  Update ag rules, ag product

  Update taxonomy parsing to allow taxonomy rules

  Update rule parsing to allow count based rules

  Update visualization to allow metaT mapping input and mapping heatmaps


## 2.0.0-beta30 - 2026-05-28

[c065dce](https://github.com/WrightonLabCSU/DRAM/commit/c065dce9a431c6fda55ab0e4a6b464fdbf0c194c)...[745c873](https://github.com/WrightonLabCSU/DRAM/commit/745c873d3d6842ce4cf8b28dfac5c737a6d93a07)

### Bug Fixes

- dbcan now passes threads argument fix ([7962c4b](https://github.com/WrightonLabCSU/DRAM/commit/7962c4b017967cfe11a57772e9a339cbd9225ad4))


- Add retry on dbcan for io concurrency problem ([7409a1b](https://github.com/WrightonLabCSU/DRAM/commit/7409a1b8952442564d577cf4db0308c0e1bd1b2b))



### Features

- Update ag summarize and visualize rules ([e040bfd](https://github.com/WrightonLabCSU/DRAM/commit/e040bfdae7a8267599877ae3fbd266aee4349850))


- Update summarize topics rules ([91e3a32](https://github.com/WrightonLabCSU/DRAM/commit/91e3a32d72d3b8fa979a32341017fb481513bcbe))



## 2.0.0-beta29 - 2026-05-22

[90dfef6](https://github.com/WrightonLabCSU/DRAM/commit/90dfef6f445011f23f4e54cdd9fff3d01f7c4d20)...[88a6fef](https://github.com/WrightonLabCSU/DRAM/commit/88a6fef1bf786666ee0755bd8d7410202e3ce4d9)

### Bug Fixes

- Fix use_* options ([3437cac](https://github.com/WrightonLabCSU/DRAM/commit/3437cac189099db170d9348300e9d6e581327b69))


- Fix bugs in format_kegg_database.py ([743bf8e](https://github.com/WrightonLabCSU/DRAM/commit/743bf8e8a038c13f361aad3be4ead4e543298436))

  1. Fix MMseqs2 output database name (kegg.mmsdb, not kegg.<date>.mmsdb)
     - The database was written as kegg.<download_date>.mmsdb but
       modules/local/annotate/mmseqs_search.nf expects the file to be named
       exactly kegg.mmsdb (it constructs the path as ${db_name}.mmsdb where
       db_name is the parent directory name "kegg"). The date suffix caused a
       "No such file or directory" error at annotation time.

  2. Fix --skip_gene_ko_link argparse definition
     - Using `type=bool` does NOT work as a flag: argparse passes the string
       "False" / "True" to bool(), and bool("False") == True. Replaced with
       `action="store_true"` so the flag behaves as intended.


- Two bugs in format_kegg_db.nf ([3afbce8](https://github.com/WrightonLabCSU/DRAM/commit/3afbce83192f05c8c9e2d16744828fc04bd2642f))

  1. Replace container that lacks mmseqs2
     - FORMAT_KEGG_DB used python_scikit-bio_scipy which does not include
       mmseqs2. The process calls mmseqs createdb / createindex, so it fails
       immediately with "No such file or directory: mmseqs". Replaced with
       python_pandas_hmmer_mmseqs2_pruned, which already carries mmseqs2 and
       is used by other annotation processes in the pipeline.

  2. Fix bash condition for skip_gene_ko_link
     - The Nextflow value passed to the process is the string "0" or "1"
       (see dram.nf). In bash, `if [ "0" ]` evaluates to TRUE because any
       non-empty string is truthy. FORMAT_KEGG_DB therefore always ran the
       --skip_gene_ko_link branch, ignoring the gene_ko_link file.
       Fixed with an explicit string comparison:
         if [ "${skip_gene_ko_link}" = "true" ]
       (see companion fix in workflows/dram.nf)


- Pass boolean string to FORMAT_KEGG_DB skip_gene_ko_link ([f4b2394](https://github.com/WrightonLabCSU/DRAM/commit/f4b23944e345b0f0834923c981b4a971736073a8))

  The companion fix for the bash condition in format_kegg_db.nf requires
  that skip_gene_ko_link be the string "true" or "false" rather than the
  integer 1 or 0.

  In bash:
    `if [ "0" ]`   -> true  (non-empty string)
    `if [ "false" ]` -> true  (still non-empty - also wrong)

  The correct pattern used in format_kegg_db.nf is:
    `if [ "${skip_gene_ko_link}" = "true" ]`

  which requires this value to be exactly the string "true" or "false".
  Changed `params.skip_gene_ko_link ? 1 : 0` to
  `params.skip_gene_ko_link ? "true" : "false"`.


- Rgi no longer outputs temp dir ([7fe178e](https://github.com/WrightonLabCSU/DRAM/commit/7fe178ee18bbdcd77298bb86ebb6c09b38372ce7))

  rgi was outputting a temp/ dir to the outdir, and if multiple
  process ended at the same time and tried to write the same
  directory name, it could cause an error.
  We don't need this dir, so I am just not writting it to the
  outir.


- Antismash,rgi,dbcan run with called_genes ([f54f848](https://github.com/WrightonLabCSU/DRAM/commit/f54f848e512c1c902b63d9c5402fe0d1f6ea2ea8))

  antismash,rgi, and dbcan3 were erroring out when ran with called_genes
  because of the way the logic was implemented. Redid the logic to define
  allow the input channels to be created conditionally or be empty to skip
  certain processes when needed.

  Cleaned up some code around rename that was involved with this and
  allowed input .fna files to be renamed as well.

  Generate gff file from input .faa file by default since it is needed for
  some new databases and it is a very quick process.



### Features

- Update dbcan to dbcan3 using run_dbcan tool ([0811137](https://github.com/WrightonLabCSU/DRAM/commit/08111371627e96f8f8ac081711c74883e947190f))

  Using the run_dbcan tooling, update our use of dbcan from
  dbcan2 to dbcan3. We will use the easysubstrate call to run the
  entire run_dbcan pipeline. This initial step just consumes the first
  stages output and does not include the CGC or easysubstrate in our
  annotation or summarize.

  Add parsing for run_dbcan output to incorporate into raw-annotations.tsv

  Add ability for dram to check DB version with added version file. This
  is an optional, per database add-on that is currently only being used
  with dbcan to ensure users are updated to dbcan3.


- Update sum topics to new sheet form ([3f1eef4](https://github.com/WrightonLabCSU/DRAM/commit/3f1eef48805f54780c284d5a426797aa9184288b))

  Update summarize topics to use assimilation_and_cofactor_metabolism,
  cellular_machinery, energy_acquisition_bioenergetics, and
  environmental_interaction_and_adaptation sheets. Each sheet
  gives out a excel sheet of their own.


- Accept gzip-compressed fasta input ([f397b4a](https://github.com/WrightonLabCSU/DRAM/commit/f397b4a3ea8c6d7e0749d3d4095c87271b423c54))

  Adds a small DECOMPRESS_FASTA module (`reformat.sh` from the bbmap
  container that other modules already use) and routes only `.gz`
  inputs through it via a channel branch on the `.gz` suffix. Plain
  fastas pass through unchanged.

  Sample-name normalisation strips both the trailing `.gz` (if present)
  and one of `.fa`/`.fna`/`.fasta` so `sample.fa` and `sample.fa.gz`
  yield the same downstream name. Outputs are identical regardless of
  input compression.

  Default `--fasta_fmt '*.f*'` already matches both plain and `.gz`
  files; schema description updated to mention this explicitly., Files:modules/local/rename/decompress_fasta.nf  (new, 20 lines)
  workflows/dram.nf                          (channel branch + mix)
  nextflow_schema.json                       (description updates)


- SLURM job-array submission for per-sample fan-out stages ([f3ef6eb](https://github.com/WrightonLabCSU/DRAM/commit/f3ef6eb915b6d34832a1d469370c507a945ad48f))

  Adds two params and a withName directive so multi-sample runs on SLURM
  collapse N sbatches into one job array per stage, sparing fair-share
  priority on shared clusters:

    params.array_size  (default 0 — disabled; local-executor safe)
    params.queue_size  (already existed; default 10)

    process {
        withName: 'DRAM:ANNOTATE:CALL:.*|DRAM:ANNOTATE:DB_SEARCH:.*|DRAM:ANNOTATE:QC:COLLECT.*' {
            array = params.slurm ? params.array_size : 0
        }
    }

  The directive is gated on params.slurm so the local / standard executor
  always sees array = 0 (a no-op) — only --slurm runs honour the user's
  array_size override. The selector covers every per-sample fan-out stage
  (CALL, DB_SEARCH, and any current or future QC:COLLECT_* subworkflow).

  Same Nextflow #6108 caveat applies — intermittent ConcurrentModification-
  Exception when arrays combine with Singularity, recoverable via -resume.



### Refactor

- Lowercase `channel` factory across subworkflows + workflows ([21e5cb8](https://github.com/WrightonLabCSU/DRAM/commit/21e5cb8f54375993a35bd2651b265b15a4bb3d1f))

  DSL2 prefers the lowercase `channel` factory function over the
  `Channel` class qualifier — both work but the lowercase form is the
  documented default and is a one-character net win on every line that
  constructs a channel. Pure cosmetic refactor, no behaviour change.

  Touches all sites currently using `Channel.empty`, `Channel.fromPath`,
  etc. across:

    subworkflows/local/{call,collect_rna,db_search,merge,qc,
                        utils_nfcore_dram_pipeline}.nf
    workflows/dram.nf



### Cleanup

- Remove old files ([1859170](https://github.com/WrightonLabCSU/DRAM/commit/1859170af162b37737b9e616cdbc3964694812ef))



## 2.0.0-beta28 - 2026-04-15

[cdfe210](https://github.com/WrightonLabCSU/DRAM/commit/cdfe210ca64eb95baf6f1acedb62f91b74630181)...[e07cd74](https://github.com/WrightonLabCSU/DRAM/commit/e07cd74e8d60fca7513f645c04d0956760c74768)

### Features

- Add antiSMASH, CARD, RGI, TCDB ([8d08d1f](https://github.com/WrightonLabCSU/DRAM/commit/8d08d1f9d54fb139eb53587754e569c4317ddc37))

  Add antiSMASH nextflow module, right now just collect antismash
  raw output while we work on incorporating raw output into
  larger pipeline
  Add rgi nextflow module, right now like antiSMASH, only
  collect raw output while we work on incorporating
  ADD CARD db processing with mmseqs
  ADD TCDB processing with mmseqs

- Add DRAM DB HMMs = ([e07cd74](https://github.com/WrightonLabCSU/DRAM/commit/e07cd74e8d60fca7513f645c04d0956760c74768))

  Add DRAM team curated HMM database as new annotation db option.
  Work in progress and testing database, but can be found on GLOBUS.

## 2.0.0-beta27 - 2026-03-18

[f03804b](https://github.com/WrightonLabCSU/DRAM/commit/f03804bca43b15e55731316c00b1c34ac328c62c)...[7d9a12d](https://github.com/WrightonLabCSU/DRAM/commit/7d9a12d225c577a6b2fb0c4d7b1ba60a5588e1e8)

### Features

- Add a test version of dbcan3 to compare against dbcan2 ([efb3cc2](https://github.com/WrightonLabCSU/DRAM/commit/efb3cc23a5478f85e449099ec37285138cc5f8b7))

  dbcan3 and dbcan3-sub test versions, will run both if run_dbcan3
  option is present.

- Switch hmmsearch to using PyHMMER search ([7d9a12d](https://github.com/WrightonLabCSU/DRAM/commit/7d9a12d225c577a6b2fb0c4d7b1ba60a5588e1e8))

  PyHMMER has better parrallelism support, directly calling
  the lower level C bindings for HMMER and rewriting how
  it parallelizes. This means that when you had cpus=4 arg, it can
  1/3 of the walltime with the exact same result.

## 2.0.0-beta26 - 2026-03-09

[605d4f5](https://github.com/WrightonLabCSU/DRAM/commit/605d4f5d619d9f373352c8f400128066edcf58ef)...[91edea7](https://github.com/WrightonLabCSU/DRAM/commit/91edea7e6974be47da036f0f8af247d3d033326a)

### Features

- Add ag heatmap output ([91edea7](https://github.com/WrightonLabCSU/DRAM/commit/91edea7e6974be47da036f0f8af247d3d033326a))

  Update dram_viz version to support new ag viz rules format.
  When users run ag summarize, output ag visualization.
  Add parameters to pass in custom rules sheets.

### Package

- Add pre-commit for lint/formatting and lint/format package ([c7c030a](https://github.com/WrightonLabCSU/DRAM/commit/c7c030ab49b72ab112c579d0653c629a24f9281a))

## 2.0.0-beta25 - 2026-03-04

[c95aa83](https://github.com/WrightonLabCSU/DRAM/commit/c95aa83c8164531af536a818359ea807cc44de67)...[d8d3cb8](https://github.com/WrightonLabCSU/DRAM/commit/d8d3cb85e5c6ca743272d7c03b0b4d78878c4280)

### Bug Fixes

- Bugfixes for using input_genes parameter ([d8d3cb8](https://github.com/WrightonLabCSU/DRAM/commit/d8d3cb85e5c6ca743272d7c03b0b4d78878c4280))

- Skip tRNA and rRNA when using input_genes unless trna and rrna
  input sheet provided since they require raw fasta file to produce.
- new parse_faa file to generate called_table summary file
  that leave error message on non-zero exit code telling people
  to check the headers metadata in case they don't match with prodigal
  output metadata.
- use the same parsing code parse_faa.sh from above to generate
  sumamry table for DRAM if using input_fasta and input_genes so
  less likely of bug in one spot isn't noticed if other is working.
- fix bugs where downstream stuff would pass dummy sheet to summarize
  and then that wouldn't properly handle it
- add ability to rename headers with input_genes with --rename flag
  with rename_headers.py script and rename_proteins.nf

## 2.0.0-beta24 - 2026-02-03

[3659fda](https://github.com/WrightonLabCSU/DRAM/commit/3659fdaa0f9779108840e3bbf97c6d196b37a7d3)...[32d0527](https://github.com/WrightonLabCSU/DRAM/commit/32d05274be6eaeaed48de6bb5a047bd67f21fea1)

### Bug Fixes

- Bugfix for excel saving when rrna or trna are None ([32d0527](https://github.com/WrightonLabCSU/DRAM/commit/32d05274be6eaeaed48de6bb5a047bd67f21fea1))

## 2.0.0-beta23 - 2026-02-01

[348e276](https://github.com/WrightonLabCSU/DRAM/commit/348e2764de7b666c0f6dcc1d82deea67d96e439b)...[852e0ae](https://github.com/WrightonLabCSU/DRAM/commit/852e0ae18ae5976e8594e8f68ed1938f7eafce9d)

### Features

- Add new DRAM rule parser submodule for traits and distill ([5e9a088](https://github.com/WrightonLabCSU/DRAM/commit/5e9a08872b590c3ac372047db46ddbaa946b8814))

  New python Lark base rule parser that defines rule grammer
  for traits grammer that can be reused for distill and product.
  This rule parser is more accurate and less error prone than
  the older traits parser completely custom coded. THis fixes
  a number of bugs where things were being double counted and not
  parsed correctly. This also allows distill, traits, and product
  eventually to all use the same rule parsing code. Rule parsing
  documentation can be found in docs/rules_parser.md or
  https://dramit.readthedocs.io/en/latest/rules_parser.html

  Rule parser is implemented with polars instead of Pandas for a
  few reasons. It is a bit faster, and it allows lazy query planning.
  The annotation df is not currently lazy (eager rn), but with plans
  to allow it to be lazy. Lazy DataFrames can be more memory efficient
  by only loading the data/columns needed, and doing query optimization
  to speed up and require less memory for intermediate steps.

- Update summarize eco Ag sheet to newly developed Ag sheet ([4937f1c](https://github.com/WrightonLabCSU/DRAM/commit/4937f1ce846b3910e5fe18264f9daca8221dd207))

- Add carbon rules to traits, save traits as excel sheet ([02de665](https://github.com/WrightonLabCSU/DRAM/commit/02de6657261fb5517b3df20985285a6b2b392fa7))

### Package

- Package cleanup. Removing old files and cleanups ([c6bae64](https://github.com/WrightonLabCSU/DRAM/commit/c6bae64a787623721ff402a38afd94bab63eb12d))

## 2.0.0-beta22 - 2025-12-17

[64da24e](https://github.com/WrightonLabCSU/DRAM/commit/64da24e51367feaffe2f643dfbb0aa602e28c5c5)...[0933424](https://github.com/WrightonLabCSU/DRAM/commit/093342450e6e49c1a706cdf2c181bd931bab7a6d)

### Bug Fixes

- A_rank from info sheet for hmm parse now parse properly ([0933424](https://github.com/WrightonLabCSU/DRAM/commit/093342450e6e49c1a706cdf2c181bd931bab7a6d))

## 2.0.0-beta21 - 2025-12-15

[3648a77](https://github.com/WrightonLabCSU/DRAM/commit/3648a77ee93cb0e5c72dee5cf3d1b6b4a38a834e)...[1106003](https://github.com/WrightonLabCSU/DRAM/commit/1106003daaab6bea519132c5232cf62c54be2a9b)

### Bug Fixes

- Rrna scan e_value and strand column order fix ([e23d09f](https://github.com/WrightonLabCSU/DRAM/commit/e23d09fc90ee3c7671a6f49a5b1d95e3a6875503))

- Traits and vis can now be ran with w/o summarize ([51f7763](https://github.com/WrightonLabCSU/DRAM/commit/51f77632f1093591785ee293f5e524cbb60270ce))

  traits and visualize if ran with annotate and without
  summarize would error ebcause of a use before definition
  error. This fixes that.

- Hmm parsing now takes top hit consistently ([1106003](https://github.com/WrightonLabCSU/DRAM/commit/1106003daaab6bea519132c5232cf62c54be2a9b))

  In the translation from DRAM1->2 and moving to nextflow,
  the code to take the tophit for the hmm search had a couple
  bugs in it depending on the hmm db. It would sometimes
  take just the first hit outputted in the data sheet,
  it would calcuate the bitscore wrong, and it wouldn't
  do the info sheets right (since it was calculating bitscore
  wrong).
  Now it reports both full sequence bitscore and domain bitscore.
  It takes the top it and also reports all other hits as well.
  All of this is done in a generic way so that adding generic hmm
  support will be trivial for next release after we fix this bug
  Also add support for metals hmm DB.

### Testing

- Add integration test for summarize ([7411f82](https://github.com/WrightonLabCSU/DRAM/commit/7411f82e6cf016beb94d52996db0559648b2a38f))

## 2.0.0-beta19 - 2025-11-21

[3c20b59](https://github.com/WrightonLabCSU/DRAM/commit/3c20b59f74e7af1a78993e8e91f31a4d8390ecd6)...[79dd74d](https://github.com/WrightonLabCSU/DRAM/commit/79dd74db3e60e1b6b3f84d8a691a5f37b4365e80)

### Bugfix

- Fix distill bugs with genome stats, and metabolism summary ([419322b](https://github.com/WrightonLabCSU/DRAM/commit/419322b0d3b54ccc98d4540f94689b69c687ee42))

  genome_stats would error out if certain arguments were not provided.
  Also fixed that the metabolism summary was adding extra columns to
  some tabs that were needed.
  Also fixed that quast stats were not being passed to distill script

## 2.0.0-beta18 - 2025-11-21

[756904d](https://github.com/WrightonLabCSU/DRAM/commit/756904df36a390847945c07aa33a6741d160ab82)...[763f71f](https://github.com/WrightonLabCSU/DRAM/commit/763f71f3baa20b14dc3bcb42a25cca4805f71e71)

### Bug Fixes

- Add back in genome_stats, fix trna counts ([8db49d1](https://github.com/WrightonLabCSU/DRAM/commit/8db49d1122fc5196b24201ffdf8130cdd816e456))

  genome_stats.tsv have been absent in DRAM2, re-add them back
  in.
  Also fix the tRNA count in the genoma_stats as mentioned in #348.
  This fixes #348.
  Add quast stats to genome stats as well.

- Small bgfixes for namespace errors, error messages, and cli ([a08a37c](https://github.com/WrightonLabCSU/DRAM/commit/a08a37c03e19ccab95f7316cd20d8e75fe381af8))

### Package

- Restructure output folders ([7b66599](https://github.com/WrightonLabCSU/DRAM/commit/7b665991b602dd8acc5611f1a5b54b15e0906df4))

  Restructure output folders to mainly ANNOTATE, SUMMARIZE, and VISUALIZE

- Rename distill to summarize ([f902264](https://github.com/WrightonLabCSU/DRAM/commit/f902264072c38350aaac7e77281862f30b58a604))

  Moving and aliad distill to summarize.
  Move call under annotate and automatically run call when annotate
  and input_fasta set.
  If summarize is set, run all distillate sheets, you can still
  manually set individual distillate sheets the old way.
  Add QC flag to run QC steps like collect_rna steps, taxa, and others
  instead of having collect_rna run automatically., BREAKING CHANGE:API changes to move towards using summarize instead
  of distill, visualize instead of product, traits indead of adjectives,
  and automatically use call when annotate with input_fasta. QC only ran
  when directed instead of automatically now as its own flag now.

- Cleanup and remove outdated files ([89b563c](https://github.com/WrightonLabCSU/DRAM/commit/89b563c58438af6dff16733de9f5f5225775035d))

- Add full_mode to profiles to run all options ([d7c55bc](https://github.com/WrightonLabCSU/DRAM/commit/d7c55bcae52f52827e917f40bb72d3c6a99b18b7))

  if you run -profile full_mode, runs all dbs and pipelines steps.
  This is a convenient shorthand.
  Also add ability to specify annotation dbs as comma seperated
  with --annon_dbs, ex: --annon_dbs kegg,merops instead of
  --use_kegg --use_merops. These option names are still subject to
  change

- Update MMSEQS2 and API documentation ([895ba8e](https://github.com/WrightonLabCSU/DRAM/commit/895ba8e0e52f2dc2afb6e47ab028f55f2f515cea))

  Update MMSEQS version from 13 to 18, which should result in a
  major speedup.
  Update some other dependencies in the annotate state as well.
  Update API documentation and usage instructions

## 2.0.0-beta17 - 2025-09-23

[1ede0d5](https://github.com/WrightonLabCSU/DRAM/commit/1ede0d53641fdd286218ea3a4b5c6a832b951905)...[ab7b133](https://github.com/WrightonLabCSU/DRAM/commit/ab7b1330ca290887d7b8d435c9b135355980689e)

### Bug Fixes

- Allow calling quast with arbitrary large no of inputs ([e965d31](https://github.com/WrightonLabCSU/DRAM/commit/e965d3100f3543aebc6d24e6a6e186522e456c09))

  Quast requires passing inputs as a space seperated list of files,
  instead of a dir or other methods. This can run into ARG_MAX limits
  So change it to passing a glob, such as `*.fa` instead. This should
  fix the problem. We might need to move to batching at some point
  for performance reasons.

### Features

- Rename ID col in GFF file ([690cff7](https://github.com/WrightonLabCSU/DRAM/commit/690cff78c978d40f5e814a2949c23ce5a8549116))

  In the Prodigal GFF file, the metadata ID field is a generated
  unique ID that is in the format 1_1, 1_2, 2_1, 2_2, etc.
  This is a problem if people concatenate all the GFFs together since
  then the unique IDs aren't unique. In DRAM1, the IDs were repalced
  with the SeqID_Genenumber. So that is what we are doing here

  We also replaced the python script that parsed the GFF into a summary
  TSV for later use in DRAM2 into a tsv and replaced with with bash
  parsing. Which benchmarking showed to be around 10-50 times faster.

## 2.0.0-beta16 - 2025-09-17

[216f992](https://github.com/WrightonLabCSU/DRAM/commit/216f99253b1fbdb2d00e70ccabeb35d71f55ab91)...[47e3eaa](https://github.com/WrightonLabCSU/DRAM/commit/47e3eaad03d476596725e3d6a398b68184e094e1)

### Features

- Add nf-test ([6f801af](https://github.com/WrightonLabCSU/DRAM/commit/6f801af84314424d1d3e5b1df083e36e59605f10))

  Add nf-test to check DRAM2 vs DRAM1 output
  as well as a way to snapshot test DRAM2 changes
  for major changes in the future.
  First tests include annotation.tsv checks and fixes.

### Bug

- Fix TRNA_COLLECT and COMBINE_ANNOTATIONS for large # inputs ([319ba9b](https://github.com/WrightonLabCSU/DRAM/commit/319ba9b7b54e756cab09c76eb3b412f93d6e7da9))

  rewrite TRNA_COLLECT to use pandas vectorized functions instead of
  embedded for loops to significantly streamline creation of
  collected_trnas.tsv with large # of inputs. Now instead of taking
  hours or days, it will run in seconds or minutes.

  rewrite COMBINTE_ANNOTATIONS to take directories of inputs instead
  of a cli list of files so that when you have thousands and
  thousands of mags or assemblies you don't run into your system's
  ARG_MAX.

## 2.0.0-beta15 - 2025-08-27

### What's Changed

- Bugfixes with passing in already called genes by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/439
  - Bugfixes with passing in rrna sheets and trna sheets
  - Bugfixees for namespace errors for starting from called genes that caused runs to crash
- Add in non hit genes back into raw annotations like they were in DRAM1 by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/439
- Allow job limits (cpu, mem, time) be controlled by config by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/440
- Add adjectives CAZy parsing and ability to pass in custom rules sheet by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/441

## 2.0.0-beta13 - 2025-07-29

### Bug Fixes

- Fix bug with combine annotations nf getting files not as paths (and not getting staged properly) ([06b5294](06b5294c25d6890ca2cef74d31bb899150177190))

### What's Changed

- Fix issues with combine annotations and distill sheets binding issues, by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/436
- Package/update nf core template by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/437

## 2.0.0-beta12 - 2025-07-08

### What's Changed

- Fix bug where merops annotation didn't extract family and distill didn't have family to use by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/433

## 2.0.0-beta11 - 2025-06-11

### What's Changed

- Add slurm_node config option (nodelist) by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/429

## 2.0.0-beta10 - 2025-06-07

### What's Changed

- Feature/adjectives MVP - Add in adjectives minimum viable product by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/423
- Add a contributing docs page by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/424
- Bugfix/merops in distill not correct - Merops wasn't showing up in Distill, revert distill implementation to DRAM1 code by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/428
- Bug discovered with Pfam annotations and distill in DRAM2, Pfam has been disabled for the time being and will be reenabled in the next release or two.

## 2.0.0-beta9 - 2025-05-22

### Bugfix

- In the last version of DRAM2, due to column renames not making it to dram_vix, cazy (dbcan), merops, and pfam all were not being process correctly from DRAM2's annotation file. This led to them just not showing up in the resulting product. Now they should show up, but still have support for the older format that is outputted in DRAM1.
  - Update dram_viz to 0.1.7 because of product bugfix about column names. See dram_viz [release 0.1.7](https://github.com/WrightonLabCSU/dram-viz/releases/tag/0.1.7)

## 2.0.0-beta7 - 2025-05-12

### What's Changed

- Prodigal mode update and quast L50 output by @madeline-scyphers in 0a82b03ea577debd5d83d0e355c61a53697f69ad
- Add camper distill option by @madeline-scyphers in 9d0f087362a6371686015451c6c6da779df16fe0
- Add check for kegg,ko,dbcan, or merops when running distill by @madeline-scyphers in 8bfbe3146dd8d00a445d70303e757ef186171253
- Update distill sheets by @jmikayla1991 in f2b5d74e7cf82251575ed99e87174247d68127e5 and e6c82c48f5a03abb1f6b9c9248b037c4dc4ec264 and 2e860f5b5a07b8a5afe4d0287ba9dd90a0c82d7f
- Docs/add sphinx by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/414
- Update sphinx theme by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/415
- Update config for nf-schema and readthedocs by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/418

## 2.0.0-beta6 - 2025-04-03

### What's Changed

- Replace sample with input_fasta for output by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/404
- Changing rename to run all fasta at once instead of 1 at a time by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/406
- Package/refactor for older nextflow by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/407
- Docs/update docs for new refactor by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/409
- Package/restructure to nf core style by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/410

### BREAKING

Old DRAM2 config no longer works, please replace with new DRAM2 config

### Summary

Move to [nf-core](https://nf-co.re) style nextflow structure. Allowing more flexibility, easier user deployment on different HPC environments and easier user customization (such as customizing memory and time per job easier). Other benefits include a community of support, developed Nextflow tools and plugins that we can and are now tapping to. Easier testing. Already written instition HPC configs, and more.

- [Add nf-core assets for slack report emails, etc.](https://github.com/WrightonLabCSU/DRAM/commit/f6ffbb2848048a63ed86f0ea7db38042d7f5a7e7)
- [Simplify annotate NF workflow](https://github.com/WrightonLabCSU/DRAM/commit/3b625a8021d6d2a5ae05cbebaa7aad9cdcf2f66d)
- [Replace sample with input_fasta for output](https://github.com/WrightonLabCSU/DRAM/commit/e61535daeeb20f81e875c2359a4931104f4e2820)
  in DRAM 1, output (like raw-annotations) like had the column fasta
  in DRAM 2 it was renamed to sample, which is incorrect since it isn't
  the sample, it is the fasta. Reverting it to fasta like in DRAM 1
  is a bit more logistically difficult because a large number of
  nf processes (nf functions), and some python files use fasta
  for the fastas file paths. So replacing sample with fasta
  would cause collisions, and therefore we would need to first
  replace all fasta keyworks with something like fasta_path
  and then all sample with fasta. This route was easier
  and probably less likely to introduce bugs.
- [Changing rename to run all fasta at once instead of 1 at a time](https://github.com/WrightonLabCSU/DRAM/commit/2c3445195332cb8bff675f3d43d5579d3d3d5a13)
  rename currently runs 1 fasta at a time which means for things
  like slurm it submits 1 job per fasta. rename takes in the realm
  of seconds. It is much more efficient to batch them together.
- [downgrade nf-schema to 2.0.1 so nextflow can be down to 23 or even 22…](https://github.com/WrightonLabCSU/DRAM/commit/2033031709749b4e532cc40daa2448a0035425d0)
  … something so known users stuck on 23.something can use DRAM 2
- [Update rename for dependencies](https://github.com/WrightonLabCSU/DRAM/commit/e7a61a562638635716b53a9a7fe5198fad87a83e)
- [Update modules code to include wave seqera container](https://github.com/WrightonLabCSU/DRAM/commit/cc9b372f1aae59fa94aabcef3944d4d37e6077e2)
  using wave-cli, with cmd
  for every module in modules/local, then adding the outputted url to
  container outputer.url for the modules nextflow script, under the conda line.
  This allows users to not just use conda, but also containers, and we don't have to build them
  Ideally this would be added to a CI, but I haven't see where nf-core is doing that with a CI yet.
- [Add kegg formatting option](https://github.com/WrightonLabCSU/DRAM/commit/45bb6dfa5c421679840e861a4faf8b3b8e5664db)
- [Add processes to modules.conf](https://github.com/WrightonLabCSU/DRAM/commit/518c1dfc5760a940b34241f468f8e25cef61a724)
  Add processes to modules.conf to add publishDir information so they output
  their contents where I want them to.
  Also added process labels to processes so that NF knows cpus, memory, and time
  limits to give different processes.
- [Add slurm option to launch with slurm executor](https://github.com/WrightonLabCSU/DRAM/commit/a55cddf07936762cb980e16fcc9a4b2e136092b8)
- [Update README with some basic install instructions](https://github.com/WrightonLabCSU/DRAM/commit/0db581c820b5dabe41a5fb6469557f7e1f6b276c)

## 2.0.0-beta5 - 2024-11-05

[f415e92](f415e92fc55d228abcc1eeff911a79e09da35adb)...[42fdba0](42fdba01108598af073b048f12a6501f92de5b73)

Fix typo causing bug in main script

## 2.0.0-beta4 - 2024-11-05

[c94d0d4](c94d0d4c5010d9885506915e6c1b37d64f3c7f83)...[f415e92](f415e92fc55d228abcc1eeff911a79e09da35adb)

### What's Changed

- Give default to ch_distill_sql_script since it is used always in annotations by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/383
- Bugfix/path creation bug by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/385
- Feature/kegg pep directory by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM/pull/387

## 2.0.0-beta3 - 2024-10-15

### What's Changed

DRAM v2 is wrapped in Nextflow due to its innate scalability on HPCs and containerization, ensuring rigorous reproducibility and version control, thus making it ideally suited for high-performance computing environments. It was also containerized to give users the option to use with Docker, Singularity or other container runtimes, or still with Conda. Databases have also now been largely preformatted for users. All of this is part of the goal making DRAM easier to install and use, as well as easier to scale.

#### Pre Beta

- Nextflow initial wrapping
- DRAM package restructuring for Nextflow
- Database preformatting changes
- Containerization

### Previous Betas from old repo

#### Beta 1

- Removed hard-coded slurm node and slurm_queue in nextflow.config by @BioRRW in https://github.com/WrightonLabCSU/DRAM2/pull/1
- Dev by @BioRRW in #2 - https://github.com/WrightonLabCSU/DRAM2/pull/13
- Visualizations/make product by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/12
- Dev by @BioRRW in https://github.com/WrightonLabCSU/DRAM2/pull/14
- Visualizations/docstrings by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/15
- Add README to visualization package by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/16
- Viz/move viz to installable package by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/20
- Feature/kegg db formatting by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/23
- Package/add docker file by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/24
- Kegg formating, docker, visualization package, dev notes by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/19

#### Beta2

- Replace many ./ paths with using NF's projectDir variable by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/25
- Config/split config by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/26
- Update docs with new install instructions by @madeline-scyphers in https://github.com/WrightonLabCSU/DRAM2/pull/27

#### Beta 3

- Move from DRAM2 name back to DRAM
- Moving DRAM Nextflow Configuration to split better between internal and user

<!-- generated by git-cliff -->
