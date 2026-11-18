# DRAM Output

This is a work in progress, but here is an updated list of output files for DRAM2 as of May 11, 2026:

<details open>
  
<summary><strong>ANNOTATE/</strong></summary>

- `raw-annotations.tsv` — Initial gene annotations; with `--mapping`, one `sample:<name>` column per sample at the end (empty for genes the mapping leaves out)  
- `raw_rrna_scan.tsv` — rRNA scan results  
- `collected_rrnas.tsv` — Filtered rRNAs  
- `collected_trnas.tsv` — Filtered tRNAs  

**Subdirectories:**
- `HMM_SEARCH/` — HMM-based functional annotation results  
- `MMSEQ2/` — Sequence similarity search results  
- `PRODIGAL/` — Gene predictions  
- `QUAST/` — Assembly quality metrics  
- `RENAMED_GFFS/` — Standardized GFF files  
- `RENAMED_HEADERS/` — Renamed FASTA headers  

</details>

<details>
<summary><strong>multiqc/</strong></summary>

- `multiqc_report.html` — Aggregated QC report (HTML)
- `multiqc_data/` — subdirectory containing tool information and multiqc log

</details>

<details>
  
<summary><strong>pipeline_info/</strong></summary>
  - contains logs, pipeline parameters, and execution traces

</details>

<details>
<summary><strong>SUMMARIZE/</strong></summary>

- `metabolism_summary.xlsx` — excel workbook showing counts per MAG of curated gene sets
- `genome_stats.tsv` — Per-genome statistics  
- `summarized_genomes.tsv` — text file with same information as the metabolism summary sheet
- `traits.xlsx` — Per-MAG Traits

</details>

<details>
<summary><strong>VISUALIZE/</strong></summary>

- `product.html`  - Interactive heatmaps — Trait-based visualizations  

</details>
