process FORMAT_KEGG_DB {
    label 'process_huge'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_scikit-bio_scipy_mmseqs2:9d5864f776f52aa0' :
        'community.wave.seqera.io/library/python_scikit-bio_scipy_mmseqs2:00f5f2307075f0e0' }"

    tag { ch_kegg_pep }

    input:
        path( ch_kegg_pep, stageAs: "kegg_pep_loc" )
        path(ch_kegg_kff, stageAs: "kegg_kff_loc")
        val(kegg_download_date)

    output:
        path( "kegg/*" )

    script:
    """
    format_kegg_database.py --kegg_loc "${ch_kegg_pep}" --kegg_kff_loc "${ch_kegg_kff}" --download_date "${kegg_download_date}" --threads ${params.threads} --output_dir kegg

    """
}
