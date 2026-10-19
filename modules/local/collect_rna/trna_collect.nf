#!/usr/bin/env nextflow

process TRNA_COLLECT {
    label 'process_small'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_barrnap_trnascan-se:e21b0760a084ff3c' :
        'community.wave.seqera.io/library/python_pandas_barrnap_trnascan-se:ed2ab26abf39304b' }"

    input:
    file combined_trnas

    output:
    path("collected_trnas.tsv"), emit: trna_collected_out
    path("raw_trna_scan.tsv"), emit: trna_combined_out, optional: true

    script:
    """
    # export constants for script
    export FASTA_COLUMN="${params.CONSTANTS.FASTA_COLUMN}"

    shopt -s nullglob  # make globs that don't match expand to nothing
    files=(*processed_trnas.tsv)

    # we use backslash here to excape nf/groovy interpolation and use bash {# feature
    if ((\${#files[@]})); then
        awk '(NR==1) || (FNR>1)' "\${files[@]}" > raw_trna_scan.tsv
    else
        touch raw_trna_scan.tsv
    fi
    trna_collect.py
    """
}
