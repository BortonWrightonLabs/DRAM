process MMSEQS_INDEX{
    label 'process_tiny'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:efbc2044ad373273' :
        'community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:0c7f6aa874829210' }"

    tag { input_fasta }

    input:
    tuple val(input_fasta), path(fasta), val(query_bytes)

    output:
    tuple val(input_fasta), path("*.mmsdb*"), val(query_bytes), emit: mmseqs_index_out

    script:
    """
    # Create temporary directory
    mkdir -p mmseqs_out/tmp

    mmseqs createdb ${fasta} ${input_fasta}.mmsdb

    """


}
