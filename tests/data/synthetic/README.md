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

Checked against the baseline (below), running every topic and ecosystem sheet and
`traits_rules.tsv`. Ecosystem Summarize rows are derived from the ecosystem Visualize
sheets: one row per Gene ID their rules look up.

| Genes | Database | Targets | `synthetic_01` | `synthetic_02` |
|---|---|---|---|---|
| `D00001` (A rank), `D00014` (B rank) | CAMPER, HMM form | summarize `D00001`, `D00014`, `D00014\|K22432` | 1 each | 0 |
| `D00014;CarE` | CAMPER, mmseqs form | summarize `D00014` | — | **0** (see below) |
| `AhyA` (A), `AlkB` (B) | CANT-HYD, HMM form | summarize `AlkB` (no sheet names `AhyA`) | `AlkB` 1 | 0 |
| `BAC0604` | CANT-HYD, mmseqs form | no rule names BAC IDs | — | 0 |
| `ExtA`–`ExtD` (`_pcc_cyt`, `_porin`, …) | FeGenie | summarize each; trait `iron-reduction` via `@ExtABCD` (`ExtB` plus a cytochrome) | all; trait ✔ | `ExtA` only; trait ✘ |
| `FoxE`, `FoxY`, `FoxZ` | FeGenie | `@foxEYZ` = `FoxE & FoxY & FoxZ` | all three | `FoxE` only |
| `Cyc2_repCluster1`, `Cyc2_repCluster2` | FeGenie | summarize each; trait `iron-oxidation` (`@Cyc2` = any one) | two; trait ✔ | one; trait ✔ |
| `MtrB_TIGR03509` | FeGenie | summarize `MtrB_TIGR03509` (`@mtoAB`) | 1 | 0 |
| `dsrA`, `dsrB` | sulfur | summarize `K11180 \| dsrA`, `K11181 \| dsrB` (topic sheets; the ecosystem sheets use `@DsrAB*` aliases of KOs) | 1 each | `dsrA` only |
| `SoxY`, `SoxZ`, `sqr_alignment` | sulfur | summarize each; trait `sulfur-oxidizer` needs `@SoxCore` (`K17224` …), which no gene has | trait ✘ | trait ✘ |
| `GH1`, `GH5`, `GH9` in `dbcan_id`, with `dbcan_sub_id` (dbCAN-sub clusters such as `GH5_e40`) and `dbcan_sub_ec` | dbCAN | summarize `GH5_e40`, `GH9;EC:3.2.1.4`; no sheet names a bare family | `GH5_e40`, `GH9;EC:3.2.1.4` 1 each | 0 (`dbcan_sub_ec` = `-`) |
| `AA3_1` as the `dbcan_id` best hit, no `AA3` gene | dbCAN | no sheet names `AA3` or `AA3_1` (see below) | — | — |
| `dbcan_EC` `EC:6.2.1.27; EC:6.2.1.25` (family `CBM50`, which no rule names) | dbCAN | summarize `EC:6.2.1.27`, `EC:6.2.1.25` | **0** (see below) | 0 |
| `dbcan_EC` `EC:1.14.13.2` alone (family `GT41`, which no rule names) | dbCAN | summarize `EC:1.14.13.2` | 1 | 0 |
| `METHYL_0016` | methyl | no rule references methyl IDs; checks the column is read | — | — |
| one gene with no annotations | — | must not count anywhere | — | — |

Traits present: `synthetic_01`: aerobic, iron-reduction, iron-oxidation;
`synthetic_02`: aerobic, iron-oxidation.

The CAMPER and CANT-HYD rank columns (`camper_score_rank`, `cant_hyd_rank`) hold A/B
values but nothing in summarize or traits reads them; ranks are applied during annotation.

## Baseline

`baseline_values.tsv` holds the values `tests/refine_values.nf.test` expects (check `synthetic_values`), recorded with every Summarize sheet. Re-recording and allowlisting: `docs/contributing.md` (Testing).

## Known gaps this fixture records

These are dram-rules parsing gaps, tracked in the dram-rules tracker under `id-parsing/`. The fixture holds today's values, so fixing them shows up as reviewable diffs at the `bin/rules` bump.

- **`AA3`** (dram-rules `id-parsing` 01): a gene whose dbCAN best hit is a subfamily (`AA3_1`) doesn't count for the family. Real DRAM2 often writes subfamily best hits to `dbcan_id`. No built-in sheet names `AA3`, so the fixture no longer shows this; a sheet that does would.
- **`EC:6.2.1.27`, `EC:6.2.1.25` = 0** (`id-parsing` 03): `dbcan_EC` isn't parsed as EC numbers, so a cell with two ECs matches neither. The single-EC gene matches only because the whole cell equals the Gene ID.
- **CAMPER mmseqs form** (`id-parsing` 02), below.

### CAMPER mmseqs IDs

CAMPER's mmseqs path writes `camper_id` as `D00014;CarE`, and dram-rules
(`ID_EXPR_DICT["camper_id"]`) uses it as one unsplit ID, so it never matches a rule
naming `D00014`. A CAMPER hit found only by mmseqs therefore doesn't count. The
`synthetic_02` row records today's behaviour (0).
