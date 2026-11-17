process ADD_BIN_QUALITY {
    label 'process_small'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_biopython:81f6b2a8fb71cdc6' :
        'community.wave.seqera.io/library/python_pandas_biopython:7df21d027f67112e' }"

    input:
    file( combined_annotations )
    file( ch_bin_quality )

    output:
    path("raw-annotations.tsv"), emit: annots_bin_quality_out, optional: true

    script:
    """
    add_bin_quality.py "${params.CONSTANTS.FASTA_COLUMN}" "${combined_annotations}" "${ch_bin_quality}" raw-annotations.tsv
    """
}
