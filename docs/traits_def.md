# Traits

`--traits` evaluates trait rules against gene annotations and writes `VISUALIZE/df_traits.tsv` and `VISUALIZE/heatmap_traits.html`. These outputs describe broad metabolic functions assigned to each MAG.
Interpret these outputs as metabolic potential inferred from gene annotations. Assemblies containing multiple organisms can combine evidence across genomes, so organism-level trait calls need extra care. Taxonomy, synteny, and other genomic context can support biological interpretation beyond the rule calls.


The checked-in trait and common rule sheets are the source of truth for current calls; see the [rule parser guide](rules_parser.md) for rule syntax. The descriptions below provide biological context and should be checked against the configured rules when interpreting an individual call.

Presence/Absence Definitions:

- Aerobic: ≥50% of NADH dehydrogenase and at least one subunit of low affinity oxidase
- Microaerophilic: ≥50% of NADH dehydrogenase and at least one subunit of high affinity oxidase
- Methanogen: These calls match those in Adrienne’s paper and are based on the presence of mcrA or taxonomy 
- ANME: Based on presence of mcrA and taxonomy
- Aerobic Methanotroph: These calls match those in Adrienne’s paper and are based on the presence of pmoA or taxonomy
- Photosynthetic: must have anaerobic PSI or anaerobic PSII or aerobic PSI or aerobic PSII
- Iron Oxidation: must have cyc2 (from cluster 1), PioA, sulfocyanin, foxEYZ, or foxABC AND this also needs oxygen or nitrate, or nitrite and greater than 50% of NADH dehydrogenase (the only exceptions were made for known iron reducers)
- Iron Reduction: must have mtrCAB, omcF, omcS, omcZ, DFE operons, or FmnA operons, and 50% of NADH dehydrogenase (the only exceptions were made for known iron reducers)
- S oxidation: dsrAB (oxidizing), soeABC, sorAB, or sqr or fccAB or soxXA or soxYZ or soxB or soxCD and 50% of NADH dehydrogenase with electron acceptor 
- S reducer: dsrAB (reducing type), phsA or ttrA
- Nitrifier: amoA or nxr (verified by gene trees) and 50% of NADH dehydrogenase with electron acceptor
- N reducer: narGH, napAB, nirKS, norBC, or nosZ and 50% of NADH dehydrogenase (except in the case of the methanotrophs, if the narG was expressed I called true in both sheets)
- DNRA: nrfAH or nirBD (can be fermentative or respiratory)
- N fixer: nifHDK, anfG, or vnfG 
- N utilization: has an nxr/nar that could not be classified

Expression Definitions
-	Aerobic: ≥30% of NADH dehydrogenase and at least one subunit of low affinity oxidase active
-	Microaerophilic: ≥30% of NADH dehydrogenase and at least one subunit of high affinity oxidase
-	Methanogen: TRUE if genome is active in the 1948 list
-	ANME: TRUE if genome is active in the 1948 list
-	Aerobic Methanotroph: TRUE if genome is active in the 1948 list
-	Photosynthetic: must have anaerobic PSI or anaerobic PSII or aerobic PSI or aerobic PSII active
-	Iron Oxidation: must have cyc2 (from cluster 1), PioA, sulfocyanin, foxEYZ, or foxABC expressed (1 gene required in one sample)
-	Iron Reduction: must have mtrCAB, omcF, omcS, omcZ, DFE operons, or FmnA operons expressed (1 gene from FeGenie expressed in one sample OR 3 genes with >3 hemes expressed in one sample)
-	S oxidation: dsrAB (oxidizing type), soeABC, sorAB, or sqr or fccAB or soxXA or soxYZ or soxB or soxCD
    - If true for both it is likely because of phsA
-	S reducer: dsrAB (reducing type), phsA or ttrA 
-	Nitrifier: amoA or nxr (both treed genes)
-	N reducer: narG, napAB, nirKS, norBC, or nosZ (except in the case of the methanotrophs, if the narG was expressed, called TRUE in both sheets)
-	DNRA: nrfAH or nirBD– can be fermentative or respiratory, one of the genes needed to be active
-	N fixer: nifHDK, anfG, or vnfG active
- N utilization: has an nxr/nar that could not be classified
-	Obligate fermenter: TRUE if genome is active in the 1948 list

*this is a living document and is subject to change*
