process RENAME {
    label 'process_tiny'

    // rename/environment.yml is bbmap-only (no python); reuse the annotate image, already pulled for annotation
    conda "${moduleDir}/../annotate/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_hmmer_mmseqs2_pruned:c0498052314d37a1' :
        'community.wave.seqera.io/library/python_pandas_hmmer_mmseqs2_pruned:5fe0d246aae33875' }"

    input:
    tuple val(fasta_names), path(fastas)

    output:
    tuple path("*_renamed_headers.tsv"), path("RENAMED_HEADERS/*"), emit: renamed_batch

    script:
    def manifest = "${task.process.tokenize(':').last()}_renamed_headers.tsv"
    // one file stages as a lone path, not a list
    def pairs = [fasta_names, [fastas].flatten()].transpose().collect { name, fasta -> "${name} ${fasta}" }.join(' ')
    """
    rename_headers.py ${manifest} RENAMED_HEADERS ${pairs}
    """
}
