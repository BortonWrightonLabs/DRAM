process COMBINE_ANNOTATIONS {
    label 'process_small'

    conda "${moduleDir}/../refine/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_bokeh_panel_click_pruned:eecc2e59dfa7eb96' :
        'community.wave.seqera.io/library/python_bokeh_panel_click_pruned:4aa7aba4b6411bd4' }"

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
