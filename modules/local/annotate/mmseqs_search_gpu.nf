process MMSEQS_SEARCH_GPU {
    label 'process_mmseqs_search'
    label 'process_gpu'
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
    val( bit_score_threshold )
    val( rbh_bit_score_threshold )
    path( db_descriptions, stageAs: 'db_descriptions.tsv' )
    val( db_name )

    output:
    tuple val(sample_names), path("mmseqs_out/*___mmseqs_${db_name}.tsv"), emit: mmseqs_search_raw_out, optional: true
    tuple val(sample_names), path("mmseqs_out/*___mmseqs_${db_name}_formatted.csv"), emit: mmseqs_search_formatted_out, optional: true

    script:
    if (query_fasta.size() != sample_names.size()) {
        error('MMseqs search batches need exactly one protein FASTA per sample')
    }
    def descriptions = sample_names.withIndex().collect { input_fasta, index ->
        """
    if [ -s "mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv" ]; then
        mmseqs_add_descriptions.py "${input_fasta}" "${db_name}" "db_descriptions.tsv" "${bit_score_threshold}" "${gene_locations[index]}" "mmseqs_out/${input_fasta}___mmseqs_${db_name}.tsv" "mmseqs_out/${input_fasta}___mmseqs_${db_name}_formatted.csv"
    fi
        """
    }.join('\n')
    """
    set -euo pipefail

    if [ "${db_name}" = "pfam" ]; then
        echo "ERROR: PFAM profile searches are CPU-only and cannot use MMSEQS_SEARCH_GPU." >&2
        exit 1
    fi

    ln -s ${mmseqs_database}/* ./

    target_db="${db_name}.mmsdb"
    target_index="\${target_db}.idx"

    if [ ! -s "\${target_db}.dbtype" ]; then
        echo "ERROR: MMseqs target database \${target_db} is missing its .dbtype file." >&2
        exit 1
    fi

    target_dbtype=\$(od -An -tu4 -N4 "\${target_db}.dbtype" | tr -d '[:space:]')
    if [ -z "\${target_dbtype}" ] || [ \$((target_dbtype & 524288)) -eq 0 ]; then
        echo "ERROR: MMseqs target database \${target_db} is not GPU-ready. Rebuild it with 'mmseqs createdb <target.faa> \${target_db} --gpu 1'." >&2
        exit 1
    fi

    if [ ! -s "\${target_index}" ] || [ ! -s "\${target_index}.index" ] || [ ! -s "\${target_index}.dbtype" ]; then
        echo "ERROR: MMseqs target database \${target_db} is missing its GPU index. Build it with 'mmseqs createindex \${target_db} <tmp> --index-subset 2'." >&2
        exit 1
    fi

    if grep -Eq '^(3|4|9|10|11|12)[[:space:]]' "\${target_index}.index"; then
        echo "ERROR: MMseqs target index \${target_index} was not built with --index-subset 2. Rebuild it with 'mmseqs createindex \${target_db} <tmp> --index-subset 2'." >&2
        exit 1
    fi

    allocated_memory_bytes=${task.memory.toBytes()}
    index_size_bytes=\$(stat -Lc '%s' "\${target_index}")
    recommended_memory_bytes=\$(((index_size_bytes * 5 + 3) / 4))

    if [ "\${allocated_memory_bytes}" -lt "\${index_size_bytes}" ]; then
        echo "ERROR: MMseqs GPU index \${target_index} is \${index_size_bytes} bytes, but this task has only \${allocated_memory_bytes} bytes of host memory. Increase the process memory allocation above the index size." >&2
        exit 1
    fi

    if [ "\${allocated_memory_bytes}" -lt "\${recommended_memory_bytes}" ]; then
        echo "WARNING: MMseqs GPU index \${target_index} is \${index_size_bytes} bytes and this task has \${allocated_memory_bytes} bytes of host memory. At least 1.25 times the index size is recommended for search overhead." >&2
    fi

    mkdir -p mmseqs_out/tmp

    # One query database for the whole batch. E-values depend only on the
    # target, so hits match per-sample searches; qsetid maps them back.
    mmseqs createdb ${query_fasta.join(' ')} query.mmsdb
    printf '%s\\n' ${sample_names.join(' ')} > batch_samples.txt

    mmseqs search query.mmsdb "\${target_db}" mmseqs_out/hits.mmsdb mmseqs_out/tmp --gpu 1 --threads ${task.cpus}
    mmseqs filterdb --filter-column 2 --comparison-operator ge --comparison-value ${bit_score_threshold} --threads ${task.cpus} mmseqs_out/hits.mmsdb mmseqs_out/passing.mmsdb
    mmseqs rmdb mmseqs_out/hits.mmsdb
    mmseqs filterdb mmseqs_out/passing.mmsdb mmseqs_out/best.mmsdb --extract-lines 1
    mmseqs rmdb mmseqs_out/passing.mmsdb
    # Convert results to BLAST outformat 6 but include target headers for description parsing if possible
    mmseqs convertalis query.mmsdb "\${target_db}" mmseqs_out/best.mmsdb mmseqs_out/batch_hits.tsv --threads ${task.cpus} --format-mode 4 --format-output "qsetid,query,target,fident,alnlen,mismatch,gapopen,qstart,qend,tstart,tend,evalue,bits,theader"
    mmseqs rmdb mmseqs_out/best.mmsdb

    split_mmseqs_batch.sh mmseqs_out/batch_hits.tsv batch_samples.txt "mmseqs_out" "___mmseqs_${db_name}.tsv"
    rm mmseqs_out/batch_hits.tsv
    ${descriptions}
    """
}
