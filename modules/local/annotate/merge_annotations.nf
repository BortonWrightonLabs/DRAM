process MERGE_ANNOTATIONS {
    label 'process_small'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:efbc2044ad373273' :
        'community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:0c7f6aa874829210' }"

    input:
    path( ch_annotations, stageAs: "annotations/*" )

    output:
    path "raw-merged-annotations.tsv", emit: ch_merged_annots_out

    script:
    """
    merge_annotations.py "${params.CONSTANTS.FASTA_COLUMN}" annotations raw-merged-annotations.tsv
    """
}
