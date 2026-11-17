# Anonymized DRAM1 run

A DRAM1 annotate + distill run of six MAGs, rewritten into DRAM2's annotation
format with all genome, scaffold and gene names replaced. Built by:

```
pixi run python tests/scripts/anonymize_dram1.py \
    --annotate <DRAM1_runs>/dram1_small_test \
    --distill <DRAM1_runs>/dram1_small_test_distill \
    --keep <genome kept whole #1> --keep <genome kept whole #2> \
    --out tests/data/dram1
```

The source run is not public; only this anonymized derivative is committed. The two
`--keep` genomes (the pair covering the most distinct KO, MEROPS and CAZy IDs) are
deliberately not named anywhere in the repo.

## What's here

| File | From DRAM1 | Notes |
|---|---|---|
| `annotations.tsv` | `annotations.tsv` | DRAM2 columns. `genome_01`/`02`: every gene. `genome_03`–`06`: only genes carrying a KO, MEROPS family or CAZy ID that `genome_01`/`02` lack. |
| `trnas/raw_trna_scan.tsv` | `trnas.tsv` | DRAM2's raw tRNA format, all six genomes, in a directory so it can be passed as `--trnas` |
| `comparable_ids.tsv` | — | The (genome, ID type, ID) pairs in `genome_03`–`06` whose Gene Counts still match DRAM1 (see below) |
| `collected_trnas.tsv` | — | `raw_trna_scan.tsv` run through `bin/trna_collect.py`, as the pipeline does |
| `baseline_values.tsv` | — | Summarize, Traits and Visualize values from DRAM2 on this fixture at `bin/rules` `1b098eb` (see below) |
| `metabolism_summary.xlsx`, `product.tsv`, `genome_stats.tsv` | distill outputs | Renamed only; still describe the **whole** six genomes |

## Comparing DRAM2 to DRAM1 with it

- `genome_01`, `genome_02`: everything is comparable.
- tRNAs: every genome (`trnas/` holds all six genomes' tRNAs).
- `genome_03`–`06`: only the Gene Counts listed in `comparable_ids.tsv`: the IDs `genome_01`/`02` lack. Every gene carrying such an ID was kept, so those counts match DRAM1. A kept gene can also carry IDs `genome_01`/`02` have; those IDs' other genes were dropped, so their counts are **not** comparable. Pathway completeness (`product.tsv`) and every other count reflect the whole genome.

## Conversion from DRAM1 columns

- `fasta` → `input_fasta`, `gene_position` → `gene_number`, `end_position` → `stop_position`
- `ko_id` → `kofam_id` (`/`-separated, as DRAM2 writes it). DRAM1 got these KOs from KEGG; the fixture treats them as KOfam, which most DRAM2 runs use and which gives nearly the same KOs
- `kegg_hit` (KEGG text) → dropped, except its complete EC numbers, which go to `kofam_EC` as `EC:x.x.x.x; EC:…` (DRAM2's EC format; partial ECs like `2.4.-.-` are dropped. Real `kofam_EC` keeps them, but dram-rules reads only complete ECs, so no count changes)
- `kegg_bitScore` → `kofam_full_bitScore` (a KEGG mmseqs score, not a KOfam HMM score)
- `kegg_genes_id`, `kegg_RBH`, `kegg_identity`, `kegg_eVal` → dropped
- `peptidase_*` → `merops_*` (RBH, identity and e-value dropped)
- `pfam_hits` → `pfam_id` (accessions) + `pfam_description` (full text)
- `cazy_ids` → `dbcan_id` (`;`-separated, families and subfamilies together, as DRAM2's dbCAN HMM search writes them; DRAM2's `dbcan_sub_id` holds dbCAN-sub clusters, which DRAM1 never ran, so it is absent); `cazy_hits` → `dbcan_description`; `cazy_subfam_ec` → `dbcan_sub_ec` (`;`-separated); `cazy_best_hit` dropped

## Checks (`tests/refine_values.nf.test`, tag `pr`)

`tests/scripts/refine_values.py` reduces Summarize, Traits and Visualize outputs to values: Gene Count per (label, Genome), and Presence/Coverage per (Rule, sheet, Genome). Files, Groups, descriptions and order are ignored, and both today's layout and Refine's are read.

- **Baseline:** values must equal `baseline_values.tsv`, recorded at `bin/rules` `1b098eb`.
- **DRAM1:** Gene Counts must equal `metabolism_summary.xlsx` for the labels both report, within the comparable values above.

At `1b098eb` the baselines hold no Coverage values (no built-in sheet reports Coverage), and the default Visualize sheet is recorded as `visualize/gut`: with every Summarize sheet run, the pipeline runs the ecosystem Visualize sheets instead, and dram-rules' default sheet is `rules_gut.tsv`. Only non-zero values are stored, so a rule that disappears from the outputs reads as 0, not as a difference.

Known differences are in `tests/data/allowlist.tsv` (checks `dram1_values` and `dram1_summarize`), one reason per line; an allowlisted value that stops differing also fails. When a change is intended, re-record with the command the failure prints:

```
pixi run python tests/scripts/refine_values.py extract <outdir> tests/data/dram1/baseline_values.tsv
```
