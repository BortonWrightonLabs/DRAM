# Mini test databases

Small subsets of the full DRAM databases, chosen from what the OWC test genomes
(`tests/data/owc/called_genes/`) hit. `tests/pr.config` points annotation at them.
Sources and licences: `LICENSES.md`.

Each folder's `ids.txt` lists what was kept, in the full database's order (hit
lists such as `kofam_ids` follow that order). Per database:

- **KOfam:** every KO that passes its `kofam_ko_list.tsv` threshold on OWC, plus the 3 best that don't.
- **VOGdb, FeGenie:** every model with an E ≤ 1e-5 hit. The pipeline gives these two a dummy info sheet, so FeGenie's `fegenie_iron_cut_offs.txt` is never read and isn't included.
- **CAMPER-HMM, dram_db:** OWC gets no annotations, so the 3 best-scoring models within the pipeline's e-value are kept to exercise the "scored but below threshold" path.
- **CANT-HYD-HMM:** OWC has no hit within E ≤ 1e-5, so only decoys. It's there because `--use_canthyd` loads both CANT-HYD databases.
- **UniRef, CANT-HYD-mmseqs, CAMPER-mmseqs:** each gene's top 5 targets. CAMPER-mmseqs has no hit ≥ 60 bits; it's there because `--use_camper` loads both CAMPER databases.
- **Every database:** 3 small models or sequences OWC never matches (decoys).

## Commands

```
# rebuild the committed files from ids.txt (needs databases/)
pixi run python tests/scripts/build_mini_dbs.py build

# re-choose ids.txt by searching OWC against databases/ (about 10 min, mostly UniRef), then build
pixi run python tests/scripts/build_mini_dbs.py select

# build the KOfam subset (not committed) from a local copy...
pixi run python tests/scripts/build_mini_dbs.py kofam \
    --profiles databases/kofam/kofam_profiles.hmm \
    --ko-list databases/kofam/kofam_ko_list.tsv --out tests/data/db/kofam
# ...or from the GenomeNet archive CI uses: --profiles profiles.tar.gz --ko-list ko_list.gz
```

## KOfam release

`kofam/ids.txt` was chosen against `databases/kofam`, which is the GenomeNet archive
`ftp://ftp.genome.jp/pub/db/kofam/archives/2022-08-01/` (its `ko_list` matches byte for byte,
and the subset built from that archive is identical to one built from the local copy).
CI builds from that archive (`KOFAM_RELEASE` in `.github/workflows/tests.yml`). Other
releases have different profiles and thresholds, so when `databases/kofam` is updated,
rerun `select` and bump `KOFAM_RELEASE` together.

## Known difference from the full databases

Annotating OWC with the HMM minis gives the same output as the full databases,
e-values included. The mmseqs minis give the same hits and bit scores, with one
exception (their e-values always differ, see below):

- **UniRef, `OWC_0001_k121_21365628_9`:** with the full database the best hit is
  `UniRef90_A0A7C4NFY4` (74 bits); with the mini it is `UniRef90_A0A662HIM1` (68 bits),
  even though both targets are in the mini. mmseqs chooses its prefilter k-mer length
  from the target database's size: 7 for the full UniRef, 6 for the mini. At k=6 the
  prefilter misses the 74-bit target. DRAM's `mmseqs search` doesn't set `-k`, so this
  is accepted rather than worked around. MMseqs e-values also scale with database
  size, so compare UniRef bit scores and hit IDs, never e-values.
