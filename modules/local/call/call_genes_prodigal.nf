process CALL_GENES {
    label 'process_call_genes'
    label 'process_array'

    tag { sample_names.join(',') }

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_scikit-bio_hmmer_pruned:0bcae53ff4ef8178' :
        'community.wave.seqera.io/library/python_pandas_scikit-bio_hmmer_pruned:ef64c488c99048d6' }"

    input:
    tuple val(resource_class), val(sample_names),
        path(fastas, stageAs: 'inputs/input??.fa', arity: '1..*')

    output:
    tuple val(sample_names), path("*_called_genes.fna"), emit: prodigal_fna, optional: true
    tuple val(sample_names), path("*_called_genes.faa"), emit: prodigal_faa, optional: true
    tuple val(sample_names), path("*_called_genes_table.tsv"), emit: prodigal_locs_tsv, optional: true
    tuple val(sample_names), path("*_${params.min_contig_len}.fa"), emit: prodigal_filtered_fasta, optional: true
    tuple val(sample_names), path("*_called_genes.gff"), emit: prodigal_gff, optional: true


    script:

    sample_names.withIndex().collect { input_fasta, index ->
        def fasta = fastas[index]
        """

    reformat.sh \\
    in=${fasta} \\
    out="${input_fasta}_${params.min_contig_len}.fa" \\
    minlength=${params.min_contig_len}

    if [ ! -s "${input_fasta}_${params.min_contig_len}.fa" ]; then
        echo "Sample ${input_fasta} - Error: no contigs after filtering for minimum contig length (${params.min_contig_len})"
        exit 1
    else

        # First we run prodigal
        prodigal \\
        -i "${input_fasta}_${params.min_contig_len}.fa" \\
        -o "${input_fasta}_called_genes.gff" \\
        -p ${params.prodigal_mode} \\
        -g ${params.prodigal_trans_table} \\
        -f gff \\
        -d "${input_fasta}_called_genes.fna" \\
        -a "${input_fasta}_called_genes.faa"

        if [ ! -s "${input_fasta}_called_genes.gff" ]; then
            echo "Sample ${input_fasta} - Warning: called genes GFF file is empty or does not exist."
            # Consider managing absent output files for downstream processes here
        else
            # With prodigal GFF output:

            # We parse the GFF to create a summary TSV for later use
            parse_faa.sh "${input_fasta}_called_genes.faa" "${input_fasta}_called_genes_table.tsv"

            # Next we need to convert all metadata ID fields from generated unique
            # IDS (1_1, 1_2, 2_1, etc.) to SeqID_GeneNumber (Bin7_1, Bin7_2, etc.)
            gff_replace_id_with_scaffold_gene_number.sh "${input_fasta}_called_genes.gff" "${input_fasta}_called_genes_renamed.gff"
            mv "${input_fasta}_called_genes_renamed.gff" "${input_fasta}_called_genes.gff"
        fi
    fi
        """
    }.join('\n')
}
