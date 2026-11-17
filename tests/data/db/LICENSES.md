# Mini test databases: sources and licences

See `README.md` for what each folder holds and how it was built.

| Folder | Source | Licence |
|---|---|---|
| `vogdb/` | [VOGDB](https://vogdb.org), Virus Orthologous Groups | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `uniref/` | [UniRef90](https://www.uniprot.org/help/uniref), UniProt Consortium | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `fegenie/` | [FeGenie](https://github.com/Arkadiy-Garber/FeGenie), Garber et al. 2020 | [AGPL-3.0](https://github.com/Arkadiy-Garber/FeGenie/blob/master/LICENSE) |
| `camper_hmm/`, `camper_mmseqs/` | [CAMPER](https://github.com/WrightonLabCSU/CAMPER), Wrighton Lab | Lab-built |
| `dram_db/` | DRAM's own HMM collection, Wrighton Lab | Lab-built |
| `canthyd_hmm/`, `canthyd_mmseqs/` | [CANT-HYD](https://github.com/dgittins/CANT-HYD-HydrocarbonBiodegradation), Khot et al. 2022 | See the source repository |
| `kofam/` | [KOfam](https://www.genome.jp/tools/kofamkoala/), GenomeNet / KEGG, release 2022-08-01 | **Not committed.** Only `ids.txt` is in git. The HMMs and `kofam_ko_list.tsv` are built locally or in CI, because KEGG-derived data may not be redistributable. |

Changes made: each database was cut down to the entries in its `ids.txt`, and score
tables were cut to the matching rows. No entry was modified.
