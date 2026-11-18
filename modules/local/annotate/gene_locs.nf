process GENE_LOCS {
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_hmmer_mmseqs2_pruned:c0498052314d37a1' :
        'community.wave.seqera.io/library/python_pandas_hmmer_mmseqs2_pruned:5fe0d246aae33875' }"

    tag { input_fasta }

    input:
    tuple val( input_fasta ), path( genes )

    output:
    tuple val( input_fasta ), path( "${input_fasta}_called_genes_table.tsv" ), emit: prodigal_locs_tsv


    script:

    """
    parse_faa.sh ${genes} "${input_fasta}_called_genes_table.tsv"
    """
}
