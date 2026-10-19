process QUAST {
    label 'process_quast'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_scikit-bio_hmmer_pruned:0bcae53ff4ef8178' :
        'community.wave.seqera.io/library/python_pandas_scikit-bio_hmmer_pruned:ef64c488c99048d6' }"

    input:
    tuple val(resource_class), path(collected_fasta_gff)

    output:
    path("quast_results/report.tsv"), emit: quast_tsv
    path("collected_quast.tsv"), emit: quast_collected_out
    path( "*.log" ), emit: log

    script:
    """
    set -euo pipefail
    shopt -s nullglob   # make *.fa expand to nothing if no matches

    export FASTA_COLUMN="${params.CONSTANTS.FASTA_COLUMN}"

    quast.py -o quast_results --no-plots --no-html --no-icarus --no-snps *.fa

    process_quast.py
    """
}
