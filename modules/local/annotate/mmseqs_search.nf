process MMSEQS_SEARCH {
    label 'process_mmseqs_search'
    label 'process_array'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_hmmer_mmseqs2_pruned:c0498052314d37a1' :
        'community.wave.seqera.io/library/python_pandas_hmmer_mmseqs2_pruned:5fe0d246aae33875' }"

    tag { sample_names.join(',') }

    input:
    tuple( val(resource_class),
        val(sample_names),
        path(query_fasta, stageAs: 'query/*', arity: '1..*'),
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
    if (query_fasta.size() != sample_names.size()) {
        error('MMseqs search batches need exactly one protein FASTA per sample')
    }
    def descriptions = sample_names.withIndex().collect { input_fasta, index ->
        """
    if [ ! -s "mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv" ]; then
        echo "The file mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv is empty. Skipping further processing."
    else
        mmseqs_add_descriptions.py "${input_fasta}" "${db_name}" "db_descriptions.tsv" "${bit_score_threshold}" "${gene_locations[index]}" "mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv" "mmseqs_out/${input_fasta}___mmseqs_${db_name}_formatted.csv"
    fi
        """
    }.join('\n')
    """
    set -euo pipefail
    ln -s ${mmseqs_database}/* ./
    mkdir -p mmseqs_out/tmp

    # One query database for the whole batch. E-values depend only on the
    # target, so hits match per-sample searches; qsetid maps them back.
    mmseqs createdb ${query_fasta.join(' ')} query.mmsdb
    printf '%s\\n' ${sample_names.join(' ')} > batch_samples.txt

    if [ "${db_name}" != "pfam" ]; then
        mmseqs search query.mmsdb ${db_name}.mmsdb mmseqs_out/hits.mmsdb mmseqs_out/tmp --threads ${task.cpus}

        # Filter to only hits with minimum bit score
        mmseqs filterdb --filter-column 2 --comparison-operator ge --comparison-value ${bit_score_threshold} --threads ${task.cpus} mmseqs_out/hits.mmsdb mmseqs_out/passing.mmsdb
        mmseqs rmdb mmseqs_out/hits.mmsdb

        # Filter to only best hit
        mmseqs filterdb mmseqs_out/passing.mmsdb mmseqs_out/best.mmsdb --extract-lines 1
        mmseqs rmdb mmseqs_out/passing.mmsdb

        mmseqs convertalis query.mmsdb ${db_name}.mmsdb mmseqs_out/best.mmsdb mmseqs_out/batch_hits.tsv --threads ${task.cpus} --format-mode 4 --format-output "qsetid,query,target,fident,alnlen,mismatch,gapopen,qstart,qend,tstart,tend,evalue,bits,theader"
        mmseqs rmdb mmseqs_out/best.mmsdb
    else
        # Profile search
        mmseqs search query.mmsdb ${db_name}.mmspro mmseqs_out/hits.mmsdb mmseqs_out/tmp -k 5 -s 7 --threads ${task.cpus}
        mmseqs convertalis query.mmsdb ${db_name}.mmspro mmseqs_out/hits.mmsdb mmseqs_out/batch_hits.tsv --threads ${task.cpus} --format-mode 4 --format-output "qsetid,query,target,fident,alnlen,mismatch,gapopen,qstart,qend,tstart,tend,evalue,bits,theader"
        mmseqs rmdb mmseqs_out/hits.mmsdb
    fi

    split_mmseqs_batch.sh mmseqs_out/batch_hits.tsv batch_samples.txt "mmseqs_out" "___mmseqs_${db_name}.tsv"
    rm mmseqs_out/batch_hits.tsv
    ${descriptions}
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
