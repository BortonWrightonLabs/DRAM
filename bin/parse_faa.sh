#!/usr/bin/env bash
set -euo pipefail

INPUT_FILE=$1
OUTPUT_FILE=$2

awk '
BEGIN { OFS="\t"; print "query_id","start_position","stop_position","strandedness","gene_number" }
/^>/ {
    split($0, a, " # ")
    id = substr(a[1], 2)          # strip leading >
    start = a[2]
    stop  = a[3]
    strand = a[4]
    gene_field = a[5]
    sub(/;.*/, "", gene_field)   # keep only ID=<scaffold>_<gene> (later fields contain "_" too)
    sub(/.*_/, "", gene_field)   # strip everything up to last underscore
    print id, start+0, stop+0, strand+0, gene_field
}' "$INPUT_FILE" > "$OUTPUT_FILE"


trap 'echo "parsing input faa files failed. Check they have all the same metadata information in the header files as Prodigal outputs. Example header line: >OWC_0000_k121_3157_1 # 2 # 580 # -1 # ID=1_1;partial=10;start_type=ATG;rbs_motif=AATAA;rbs_spacer=15bp;gc_cont=0.439"; exit 1' ERR
