process SUMMARIZE {
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_bokeh_panel_click_pruned:51f8873f5a533b04' :
        'community.wave.seqera.io/library/python_bokeh_panel_click_pruned:5f117a69db01d17e' }"

    input:
    path( ch_combined_annotations, stageAs: "raw-annotations.tsv" )
    path( ch_trna_combined)
    val( distill_topic )
    val( distill_ecosystem )
    val( distill_custom )

    output:
    path( "*.xlsx" ), emit: distillate
    path( "*.log" ), emit: log
    path( "summarized_genomes.tsv" ), emit: summarized_genomes

    script:
    """
    # export constants for script
    export FASTA_COLUMN="${params.CONSTANTS.FASTA_COLUMN}"

    distill.py -i ${ch_combined_annotations} --trna_path '${ch_trna_combined}' --distill_topics "${distill_topic}" --distill_ecosystem "${distill_ecosystem}" --custom_distillate "${distill_custom}"

    """
}
