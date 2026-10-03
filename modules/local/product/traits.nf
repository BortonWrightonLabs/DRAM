process TRAITS {
    label 'process_small'

    errorStrategy 'finish'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_dram-viz:2f4dc05eb05107db' :
        'community.wave.seqera.io/library/python_dram-viz:c3ddf425b4b554b9' }"

    input:
    path( ch_combined_annotations, stageAs: "raw-annotations.tsv" )
    path( rules_tsv )
    path( common_rules_tsv )

    output:
    path("heatmap_traits.html"), emit: traits_html
    path("df_traits.tsv"), emit: traits_df

    script:
    def args = task.ext.args ?: ""

    """

    dram_viz \\
        --annotations ${ch_combined_annotations} \\
        --save_dataframes \\
        -r ${rules_tsv} \\
        -c ${common_rules_tsv} \\
        $args

    mv heatmap_*.html heatmap_traits.html
    mv df_*.tsv df_traits.tsv
    """
}
