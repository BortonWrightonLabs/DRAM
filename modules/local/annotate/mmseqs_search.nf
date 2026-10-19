process MMSEQS_SEARCH {
    label 'process_mmseqs_search'
    label 'process_array'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:1742d882bc99fed5' :
        'community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:6d5bc9dfeca29b70' }"

    tag { sample_names.join(',') }

    input:
    tuple( val(resource_class),
        val(sample_names),
        path(query_database, stageAs: 'query_database/*', arity: '1..*'),
        path(gene_locations, stageAs: 'locations/genes??.tsv', arity: '1..*')
        )
    path( mmseqs_database )
    val( bit_score_threshold)
    val( rbh_bit_score_threshold )
    path( db_descriptions, stageAs: "db_descriptions.tsv" )
    val( db_name )


    output:
    tuple val(sample_names), path("mmseqs_out/*___mmseqs_${db_name}.tsv"), emit: mmseqs_search_raw_out, optional: true
    tuple val(sample_names), path("mmseqs_out/*___mmseqs_${db_name}_formatted.csv"), emit: mmseqs_search_formatted_out, optional: true
    //tuple val( input_fasta ), path("mmseqs_out/${input_fasta}___mmseqs_rbh_${db_name}.tsv "), emit: mmseqs_search_rbh_formatted_out, optional: true

    script:
    def query_names = query_database.collect { it.fileName.toString() }
    if (query_names.unique(false).size() != query_names.size()) {
        error('MMseqs query database filenames must be unique within a search batch')
    }
    def searches = sample_names.withIndex().collect { input_fasta, index ->
        def prodigal_locs_tsv = gene_locations[index]
        """

    # Create temporary directory
    mkdir -p mmseqs_out/tmp

    if [ "${db_name}" != "pfam" ]; then
        # Perform search
        mmseqs search query_database/${input_fasta}.mmsdb ${db_name}.mmsdb mmseqs_out/${input_fasta}_${db_name}.mmsdb mmseqs_out/tmp --threads ${task.cpus}

        # Filter to only hits with minimum bit score
        mmseqs filterdb --filter-column 2 --comparison-operator ge --comparison-value ${bit_score_threshold} --threads ${task.cpus} mmseqs_out/${input_fasta}_${db_name}.mmsdb mmseqs_out/passing.mmsdb

        mmseqs rmdb mmseqs_out/${input_fasta}_${db_name}.mmsdb

        # Filter to only best hit
        mmseqs filterdb mmseqs_out/passing.mmsdb mmseqs_out/best.mmsdb --extract-lines 1

        mmseqs rmdb mmseqs_out/passing.mmsdb

        # Convert results to BLAST outformat 6
        mmseqs convertalis query_database/${input_fasta}.mmsdb ${db_name}.mmsdb  mmseqs_out/best.mmsdb mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv --threads ${task.cpus}

        mmseqs rmdb mmseqs_out/best.mmsdb

        # if statement for kegg rbh goes here
    elif [ "${db_name}" == "pfam" ]; then
        # Do profile search:
        mmseqs search query_database/${input_fasta}.mmsdb ${db_name}.mmspro mmseqs_out/${input_fasta}_${db_name}.mmsdb mmseqs_out/tmp -k 5 -s 7  --threads ${task.cpus}

        # Convert results to BLAST outformat 6
        mmseqs convertalis query_database/${input_fasta}.mmsdb ${db_name}.mmspro mmseqs_out/${input_fasta}_${db_name}.mmsdb mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv --threads ${task.cpus}
    fi

    # Check if the mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv file is empty
    if [ ! -s "mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv" ]; then
        echo "The file mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv is empty. Skipping further processing."
    else
        # Call Python script for further processing
        mmseqs_add_descriptions.py "${input_fasta}" "${db_name}" "db_descriptions.tsv" "${bit_score_threshold}" "${prodigal_locs_tsv}" "mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv" "mmseqs_out/${input_fasta}___mmseqs_${db_name}_formatted.csv"
    fi

        """
    }.join('\n')
    """
    ln -s ${mmseqs_database}/* ./
    ${searches}
    """
}

/*  Code for kegg RBH - this mayt or may not work, it takes FOREVER to do the reverse search... will test later on riviera
        if [ "${db_name}" == "kegg" ]; then
            # Perform Reverse Best Hit search
            mmseqs search ${db_name}.mmsdb query_database/${input_fasta}.mmsdb  mmseqs_out/${input_fasta}_rbh_${db_name}.mmsdb mmseqs_out/tmp --threads ${task.cpus}

            # Filter Reverse Best Hit to only best hit
            mmseqs filterdb mmseqs_out/${input_fasta}_rbh_${db_name}.mmsdb mmseqs_out/${input_fasta}_${db_name}_rbh_tophit.mmsdb --extract-lines 1

            # Filter Reverse Best Hit  to only hits with minimum bit score
            mmseqs filterdb --filter-column 2 --comparison-operator ge --comparison-value ${rbh_bit_score_threshold} --threads ${task.cpus} mmseqs_out/${input_fasta}_${db_name}_rbh_tophit.mmsdb mmseqs_out/${input_fasta}_${db_name}_tophit_rbh_minbitscore${bit_score_threshold}.mmsdb

            # Convert Reverse Best Hit  results to BLAST outformat 6
            mmseqs convertalis ${db_name}.mmsdb query_database/${input_fasta}.mmsdb mmseqs_out/${input_fasta}_${db_name}_tophit_rbh_minbitscore${bit_score_threshold}.mmsdb mmseqs_out/${input_fasta}___mmseqs_rbh_${db_name}.tsv --threads ${task.cpus}

            # Need additional processing for KEGG RBH
            rbh_mmseqs_filter.py filterdb "mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv" --reverse "mmseqs_out/${input_fasta}___mmseqs_rbh_${db_name}.tsv" --output "mmseqs_out/${input_fasta}___mmseqs_rbh_${db_name}_combined.tsv"
            mv mmseqs_out/${input_fasta}___mmseqs_rbh_${db_name}_combined.tsv mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv
        fi

*/
