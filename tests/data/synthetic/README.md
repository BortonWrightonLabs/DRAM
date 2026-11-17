# Synthetic annotations

`annotations.tsv` is a hand-built DRAM2 annotations table (50 genes, two genomes)
covering databases that neither OWC nor the DRAM1 fixture annotate: CAMPER, CANT-HYD,
FeGenie, sulfur, methyl and dbCAN. Values use the formats real DRAM2 runs write.

- `synthetic_01` has every targeted gene.
- `synthetic_02` is a near miss: one gene short of several combination rules, so the
  rules' boundaries are tested in both directions.

Both genomes also carry 7 of the 14 Complex IB KOs (`@ETC50`) and `K02275`
(`@CytochromeCOxidase`), so the traits below fail only because of the
target-database genes.

## What each part targets

Checked by running `bin/distill.py` (all topics and ecosystems) and `dram_viz.py`
with `traits_rules.tsv` at `bin/rules` `1b098eb`.

| Genes | Database | Targets | `synthetic_01` | `synthetic_02` |
|---|---|---|---|---|
| `D00001` (A rank), `D00014` (B rank) | CAMPER, HMM form | summarize `D00001`, `D00014`, `D00014\|K22432` | 1 each | 0 |
| `D00014;CarE` | CAMPER, mmseqs form | summarize `D00014` | — | **0** (see below) |
| `AhyA` (A), `AlkB` (B) | CANT-HYD, HMM form | summarize `AhyA`, `AlkB`, `AlkB\|AlmA_GroupI\|…` | 1, 1, 2 | 0 |
| `BAC0604` | CANT-HYD, mmseqs form | no rule names BAC IDs | — | 0 |
| `ExtA`–`ExtD` (`_pcc_cyt`, `_porin`, …) | FeGenie | summarize each; trait `iron-reduction` via `@ExtABCD` (any one) | all; trait ✔ | `ExtA` only; trait ✔ |
| `FoxE`, `FoxY`, `FoxZ` | FeGenie | `@foxEYZ` = `FoxE & FoxY & FoxZ` | all three | `FoxE` only |
| `Cyc2_repCluster1`, `Cyc2_repCluster2` | FeGenie | `@Cyc2` = `at_least(2, COUNTS, …)`; trait `iron-oxidation` | two; trait ✔ | one; trait ✘ |
| `MtrB_TIGR03509` | FeGenie | summarize `MtrB_TIGR03509` (`@mtoAB`) | 1 | 0 |
| `dsrA`, `dsrB` | sulfur | summarize `dsrA`, `dsrB`, `HMM@dsrA`, `K11180 \| dsrA`, … | 1 each | `dsrA` only |
| `SoxY`, `SoxZ`, `sqr_alignment` | sulfur | summarize each; trait `sulfur-oxidizer` via `@SoxYZ`, `@Sqr` | trait ✔ | trait ✘ |
| `GH1`, `GH5`, `GH9` in `dbcan_id`, with `dbcan_sub_id` (dbCAN-sub clusters such as `GH5_e40`) and `dbcan_sub_ec` | dbCAN | summarize `GH1`, `GH5`, `GH9` | 1 each | `GH9` only (`dbcan_sub_ec` = `-`) |
| `AA3_1` as the `dbcan_id` best hit, no `AA3` gene | dbCAN | summarize `AA3_1` counts; family `AA3` doesn't (see below) | `AA3_1` 1, `AA3` **0** | 0 |
| `dbcan_EC` `EC:6.2.1.27; EC:6.2.1.25` (family `CBM50`, which no rule names) | dbCAN | summarize `EC:6.2.1.27`, `EC:6.2.1.25` | **0** (see below) | 0 |
| `dbcan_EC` `EC:1.14.13.2` alone (family `GT41`, which no rule names) | dbCAN | summarize `EC:1.14.13.2` | 1 | 0 |
| `METHYL_0016` | methyl | no rule references methyl IDs at `1b098eb`; checks the column is read | — | — |
| one gene with no annotations | — | must not count anywhere | — | — |

Traits present: `synthetic_01`: aerobic, iron-reduction, iron-oxidation, sulfur-oxidizer;
`synthetic_02`: aerobic, iron-reduction.

The CAMPER and CANT-HYD rank columns (`camper_score_rank`, `cant_hyd_rank`) hold A/B
values but nothing in summarize or traits reads them at `1b098eb`; ranks are applied
during annotation.

## Baseline

`baseline_values.tsv` holds the values `tests/refine_values.nf.test` expects (Gene Counts, Presence/Coverage), recorded at `bin/rules` `1b098eb` with every Summarize sheet; see `tests/data/dram1/README.md` for the comparator and re-recording. Known differences go in `tests/data/allowlist.tsv` under check `synthetic_values`.

## Known gaps this fixture records

These are dram-rules parsing gaps, tracked in the dram-rules tracker under `id-parsing/`. The fixture holds today's values, so fixing them shows up as reviewable diffs at the `bin/rules` bump.

- **`AA3` = 0** (dram-rules `id-parsing` 01): a gene whose dbCAN best hit is a subfamily (`AA3_1`) doesn't count for the family. Real DRAM2 often writes subfamily best hits to `dbcan_id`.
- **`EC:6.2.1.27`, `EC:6.2.1.25` = 0** (`id-parsing` 03): `dbcan_EC` isn't parsed as EC numbers, so a cell with two ECs matches neither. The single-EC gene matches only because the whole cell equals the Gene ID.
- **CAMPER mmseqs form** (`id-parsing` 02), below.

### CAMPER mmseqs IDs

CAMPER's mmseqs path writes `camper_id` as `D00014;CarE`, and dram-rules
(`ID_EXPR_DICT["camper_id"]`) uses it as one unsplit ID, so it never matches a rule
naming `D00014`. A CAMPER hit found only by mmseqs therefore doesn't count. The
`synthetic_02` row records today's behaviour (0).
