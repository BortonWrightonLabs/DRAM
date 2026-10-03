process PRODUCT_HEATMAP {
    label 'process_small'

    errorStrategy 'finish'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_dram-viz:2f4dc05eb05107db' :
        'community.wave.seqera.io/library/python_dram-viz:c3ddf425b4b554b9' }"

    input:
    path(ch_final_annots, stageAs: "raw-annotations.tsv")
    val(fasta_column)
    path(rules_tsv)
    path(common_rules_tsv)
    path(mapping_file)
    val(rules_system)  // comma seperated list

    output:
    path( "*.html" ), emit: product_html
    path( "*.tsv" ), emit: product_dataframes

    script:
    def args = task.ext.args ?: ''
    def viz_rules_tsv = rules_tsv ? "--rules_tsv $rules_tsv" : ''
    def viz_mapping_file = mapping_file ? "--mapping $mapping_file" : ''

    def rules_system_values = rules_system?.trim() ?
        rules_system.split(',').collect { it.trim() } :
        ['']

    def dram_viz_commands = rules_system_values.collect { rules_system_value ->
        def viz_rules_system = rules_system_value ? "--rules_system $rules_system_value" : ''
        def output_prefix = rules_system_value ? "heatmap_${rules_system_value}_" : 'heatmap_'
        def dataframe_rules_system = rules_system_value ?: (rules_tsv ? '' : 'default')
        def dataframe_suffix = dataframe_rules_system ? "_${dataframe_rules_system}" : ''
        """
        dram_viz \\
            --annotations ${ch_final_annots} \\
            --fasta_column ${fasta_column} \\
            --save_dataframes \\
            -c  ${common_rules_tsv} \\
            $viz_rules_tsv \\
            $viz_mapping_file \\
            $viz_rules_system \\
            $args

        for heatmap_file in heatmap_*.html; do
            mv "\$heatmap_file" "product_outputs/${output_prefix}\${heatmap_file#heatmap_}"
        done

        for dataframe_file in *df_*.tsv; do
            mv "\$dataframe_file" "product_outputs/\${dataframe_file%.tsv}${dataframe_suffix}.tsv"
        done
        """
    }.join("\n")

    """
    mkdir -p product_outputs
    $dram_viz_commands
    mv product_outputs/* .
    """
}
