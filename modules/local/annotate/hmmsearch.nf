process HMM_SEARCH {
    label 'process_hmm_search'
    label 'process_array'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:1742d882bc99fed5' :
        'community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:6d5bc9dfeca29b70' }"

    tag { sample_names.join(',') }

    input:
    tuple val(resource_class), val(sample_names),
        path(query_fastas, stageAs: 'queries/query??.faa', arity: '1..*'),
        path(gene_locations, stageAs: 'locations/genes??.tsv', arity: '1..*')
    val ( e_value )
    path( database_loc )
    path( hmm_info_path )
    val (ec_from_info )
    val (db_name)

    output:
    tuple val(sample_names), path("*___formatted_${db_name}_hits.csv"), emit: formatted_hits, optional: true

    script:
    def args = task.ext.args ?: ""
    def ec_flag = ec_from_info ? "--ec_from_info" : ""
    def cutoff_flag = e_value ? "--e_value ${e_value}" : ""

    sample_names.withIndex().collect { input_fasta, index ->
        def fasta = query_fastas[index]
        def prodigal_locs_tsv = gene_locations[index]
        """
    hmm_search.py \\
        --hmm  ${database_loc} \\
        --input_file ${fasta} \\
        ${cutoff_flag} \\
        --output_file ${input_fasta}_hmmsearch.out \\
        --cpus ${task.cpus}

    hmm_parser.py \\
        --hmm_domtbl ${input_fasta}_hmmsearch.out \\
        --hmm_info_path ${hmm_info_path} \\
        ${ec_flag} \\
        --gene_locs ${prodigal_locs_tsv} \\
        --db_name ${db_name} \\
        --output "${input_fasta}___formatted_${db_name}_hits.csv"
        """
    }.join('\n')
}
