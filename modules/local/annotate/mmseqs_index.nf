process MMSEQS_INDEX{
    label 'process_tiny'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:1742d882bc99fed5' :
        'community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:6d5bc9dfeca29b70' }"

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
