#!/usr/bin/env bash
# Split a batch convertalis TSV (format-mode 4, first column qsetid) into one
# file per sample. Line N of samples (0-based) is the sample whose FASTA was
# file N given to `mmseqs createdb`. Every sample gets the header, as a
# per-sample convertalis would write even with no hits.
# Usage: split_mmseqs_batch.sh <batch.tsv> <samples.txt> <out_dir> <suffix>
set -euo pipefail
batch=$1 samples=$2 out_dir=$3 suffix=$4

# Stable sort keeps convertalis' row order within each sample.
{ head -n 1 "$batch"; tail -n +2 "$batch" | sort -s -k1,1n; } | awk -F'\t' -v dir="$out_dir" -v suffix="$suffix" '
    BEGIN { id = -1 }  # uninitialised would equal qsetid 0
    NR == FNR { out[FNR - 1] = dir "/" $0 suffix; n = FNR; next }
    FNR == 1 {
        if ($1 != "qsetid") { print "first column must be qsetid" > "/dev/stderr"; exit 1 }
        sub(/^[^\t]*\t/, "")
        for (i = 0; i < n; i++) { print > out[i]; close(out[i]) }
        next
    }
    $1 != id {
        if (file) close(file)
        id = $1
        if (!(id in out)) { print "qsetid " id " has no sample" > "/dev/stderr"; exit 1 }
        file = out[id]
    }
    { sub(/^[^\t]*\t/, ""); print >> file }
' "$samples" -
