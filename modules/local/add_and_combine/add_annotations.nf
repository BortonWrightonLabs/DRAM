process ADD_ANNOTATIONS {
    label 'process_small'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_biopython:81f6b2a8fb71cdc6' :
        'community.wave.seqera.io/library/python_pandas_biopython:7df21d027f67112e' }"

    input:
    path( old_annotations, stageAs: "old_annotations.tsv" )
    path( new_annotations, stageAs: "new_annotations.tsv" )


    output:
    path "raw-combined-annotations.tsv", emit: combined_annots_out

    script:
    """
    add_annotations.py "${params.CONSTANTS.FASTA_COLUMN}" old_annotations.tsv new_annotations.tsv raw-combined-annotations.tsv
    """
}
