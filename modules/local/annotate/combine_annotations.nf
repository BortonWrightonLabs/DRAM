process COMBINE_ANNOTATIONS {
    label 'process_small'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:efbc2044ad373273' :
        'community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:0c7f6aa874829210' }"

    input:
    path(fastas, stageAs: "annotations/*" )
    path(genes, stageAs: "genes/*" )
    path(dbcan_output, stageAs: "dbcan/*")
    path(rgi_output, stageAs: "rgi/*")

    output:
    path "raw-annotations.tsv", emit: combined_annotations_out
    path( "*.log" ), emit: log

    script:
    """
    export FASTA_COLUMN="${params.CONSTANTS.FASTA_COLUMN}"

    combine_annotations.py \\
        --annotations_dir annotations \\
        --genes_dir genes \\
        --dbcan_dir dbcan \\
        --rgi_dir rgi \\
        --output raw-annotations.tsv

    """
}
