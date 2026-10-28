# Introduction to DRAM2

Welcome to the wiki for Distilling and Refining Annotations of Metabolism 2 (DRAM2)!

## Introduction

DRAM2 (Distilling and Refining Annotations of Metabolism, version 2) is a tool for annotating genomic and metagenomic assemblies (e.g., scaffolds or contigs) as well as predicted genes (nucleotide or amino acid sequences). It organizes genome annotations into metabolic functions across three levels of increasing interpretation: (1) **ANNOTATE**, (2) **SUMMARIZE**, and (3) **VISUALIZE**. The **ANNOTATE** output contains all database hits for every gene in each genome, generating a comprehensive output of most annotation pipelines. DRAM2 extends beyond this by organizing (**SUMMARIZE**) and visualizing (**VISUALIZE**) annotations into ecosystem-relevant functional categories, enabling more interpretable comparisons across genomes and ecosystems. The DRAM2 workflow enables the analysis of large numbers of microbial genomes or metagenomes, highlighting functional guilds and supporting inference of organismal metabolism across datasets.

## DRAM2 Overview & Workflow

The DRAM2 workflow is outlined below:

- Start with [installation and SLURM setup](installation.md), then see [usage and custom configuration](usage.md).
- A complete list of pipeline configuration parameters can be found here: [Parameters API](https://dramit.readthedocs.io/en/latest/params_doc.html)

**DRAM2 workflow**

1) Gene calling  
2) Gene annotation  
3) Summarize gene annotations based on curated datasets to ascribe function to MAGs  
4) Generate an interactive heatmap of ecosystem-relevant MAG level metabolic function  

**1) Gene calling**

DRAM2 uses Prodigal(v2.6.3) to find open reading frames (ORFs) from genomes, Metagenome Assembled Genomes (MAGs), or assemblies for downstream annotation. Alternatively, users can supply genes called using another platform.

**2) Gene annotation**

DRAM2 annotates genes in each genome (or Metagenome Assembled Genome (MAG)) using a suite of user-defined databases, including [KEGG](https://www.kegg.jp/) (if provided by the user), [UniRef90](https://www.uniprot.org/), [PFAM](https://pfam.xfam.org/), [dbCAN3](http://bcb.unl.edu/dbCAN2/), [RefSeq Viral](https://www.ncbi.nlm.nih.gov/genome/viruses/), [VOGDB](http://vogdb.org/), [MEROPS](https://www.ebi.ac.uk/merops/), and optional user-defined databases. A full list of available annotation databases can be found here: [BortonWrightonLabs/dram pipeline parameters](https://dramit.readthedocs.io/en/latest/params_doc.html#pipeline-steps). ANNOTATE then integrates results across all databases, increasing annotation coverage and yielding ~25% more database hits than commonly used annotators such as DFAST, MetaERG, and Prokka. The output of this step (“raw-annotations.tsv”) contains all database annotations. DRAM2 also generates ANNOTATE folder containing: (1) the annotated nucleotide and amino acid fasta files of all genes, (2) genome quality data generated via QUAST, (3) .gff files for each genome, and (4) database-specific files produced during the gene annotation process (i.e. HMMsearch output, MMseq2s output, dbcan3-hmm and dbcan3SUB-hmm etc).

**3) Summarize gene annotations based on curated datasets to ascribe function to MAGs**

After genes have been annotated, users can SUMMARIZE this information into a user-friendly excel workbook (metabolism_summary.xlsx), which contains consolidated gene counts for the most informative genes for specific metabolic functions (*Energy acquisition/bioenergetics, Assimilation & Cofactor Metabolism, Cellular Machinery & Environmental Interaction & Adaptation*). This information can be further refined using a user-defined ecosystem (*agriculture, engineered systems, biogeochemistry, and gut*) to provide the user with counts for a refined set of genes directly related to their ecosystem of interest. In addition to the metabolism_summary excel workbook, the SUMMARIZE contains three key files: (1) a genome statistics table which includes all statistics required to meet MIMAG criteria (genome_stats.tsv), (2) a metabolism summary sheet which contains gene counts of functional genes across a curated set of metabolisms and ecosystems (summarized_genomes.tsv), and (3) separate trait outputs, generated with `--traits`, describing environmentally relevant pathways (`VISUALIZE/df_traits.tsv` and `VISUALIZE/heatmap_traits.html`)

**4) Generate an interactive heatmap of ecosystem-relevant MAG level metabolic function**

Users can also generate an interactive heatmap depicting the presence of specific metabolic functions. DRAM2 automatically generates this heatmap for each ecosystem if indicated by the user in addition to a generic heatmap of metabolic function by MAG if no ecosystem is defined.

---

## Basic usage

Below is an example of basic DRAM2 usage. This code is for annotating a directory of genomes, renaming them for downstream use, calling genes and annotating them using all available databases, performing quality control, summarizing and visualizing with particular ecosystems in mind and assigning genome-level traits to the organisms. This example uses the DRAM2 `dev` branch and runs the driver in the background. Configure `cluster.config` for your SLURM allocation and database paths first. Use `-bg` only where your cluster permits persistent background drivers; see the [usage guide](usage.md#launching-directly-or-in-the-background).

```bash
nextflow run BortonWrightonLabs/DRAM -r dev --input_fasta [INPUT_FASTA] --outdir [OUTPUT_DIR] --rename --call --annotate --anno_dbs all --qc --summarize --sum_ecos 'eng_sys,ag' --visualize --traits -profile apptainer,slurm -c cluster.config -resume -bg
```

`--input_fasta` should be a directory of genomes or MAGs in FASTA format. `--anno_dbs all` selects databases with existing configured paths and warns and skips missing paths. For reproducible analyses, pin a DRAM2 tag or commit and select databases explicitly. It is also worth noting that all Nextflow options are specified with a single dash -, while all DRAM2-specific options are specified with a double dash --.

All available Nextflow options can be seen by running:
nextflow run -help

---

## Other DRAM products

DRAM webinar: https://www.youtube.com/watch?v=-Ky2fz2vw2s  
DRAM in KBase publication (2023): https://pubmed.ncbi.nlm.nih.gov/36857575/  

---

## Citing DRAM

If DRAM2 helps you in your research, please cite:
DRAM publication in Nucleic Acids Research (2020):  
https://academic.oup.com/nar/article/48/16/8883/5884738
