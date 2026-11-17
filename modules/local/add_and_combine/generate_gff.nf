process GENERATE_GFF {
    label 'process_tiny'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_biopython:81f6b2a8fb71cdc6' :
        'community.wave.seqera.io/library/python_pandas_biopython:7df21d027f67112e' }"

    input:
    tuple val(fasta_names), path(input_genes)

    output:
    tuple path("*_generated_gff.tsv"), path("GFF/*"), emit: generated_gff_batch


    script:
    // Correct usage: Directly use params without ${...} for Groovy code
    def manifest = "${task.process.tokenize(':').last()}_generated_gff.tsv"

    def cmds = fasta_names.indices.collect { i ->
        def name = fasta_names[i]
        def file = input_genes[i]
        def output = "${name}.gff"
        """
        generate_gff.py ${file} > GFF/${output}
        printf '%s\\t%s\\n' '${name}' '${output}' >> ${manifest}
        """
    }.join("\n")

    """
    mkdir -p GFF
    : > ${manifest}
    ${cmds}
    """
}
