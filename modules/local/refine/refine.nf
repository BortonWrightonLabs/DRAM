process REFINE {
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_bokeh_panel_click_pruned:51f8873f5a533b04' :
        'community.wave.seqera.io/library/python_bokeh_panel_click_pruned:5f117a69db01d17e' }"

    input:
    path( annotations, stageAs: "raw-annotations.tsv" )
    path( trnas, stageAs: "trnas.tsv" )
    val( options )  // refinement flags and built-in sheet choices, as dram-rules options
    path( viz_custom, stageAs: "viz_custom/*" )
    path( traits_custom, stageAs: "traits_custom/*" )
    path( sum_custom, stageAs: "sum_custom/*" )
    path( descriptions, stageAs: "descriptions/*" )
    path( mapping )
    path( common_rules_tsv )

    output:
    path( "{SUMMARIZE,VISUALIZE,TRAITS}/**" ), emit: outputs

    script:
    def args = task.ext.args ?: ''
    // dram-rules takes comma-separated sheets and names each output folder after the file
    def sheets = { flag, files -> files ? "${flag} ${[files].flatten().join(',')}" : '' }
    """
    dram-rules \\
        --annotations ${annotations} \\
        --fasta_column ${params.CONSTANTS.FASTA_COLUMN} \\
        --trna_path ${trnas} \\
        --output_dir out \\
        ${options} \\
        ${sheets('--viz_custom', viz_custom)} \\
        ${sheets('--traits_custom', traits_custom)} \\
        ${sheets('--sum_custom', sum_custom)} \\
        ${sheets('--descriptions', descriptions)} \\
        ${mapping ? "--mapping ${mapping}" : ''} \\
        ${common_rules_tsv ? "--common_rules_tsv ${common_rules_tsv}" : ''} \\
        $args

    # Publish each refinement's folder in upper case, like ANNOTATE/
    for refinement in out/*; do
        mv "\$refinement" "\$(basename "\$refinement" | tr a-z A-Z)"
    done
    """
}
