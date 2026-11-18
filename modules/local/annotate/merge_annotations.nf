process MERGE_ANNOTATIONS {
    label 'process_small'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_hmmer_mmseqs2_pruned:c0498052314d37a1' :
        'community.wave.seqera.io/library/python_pandas_hmmer_mmseqs2_pruned:5fe0d246aae33875' }"

    input:
    path( ch_annotations, stageAs: "annotations/*" )

    output:
    path "raw-merged-annotations.tsv", emit: ch_merged_annots_out

    script:
    """
    merge_annotations.py "${params.CONSTANTS.FASTA_COLUMN}" annotations raw-merged-annotations.tsv
    """
}
