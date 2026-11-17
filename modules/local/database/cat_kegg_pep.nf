process CAT_KEGG_PEP {

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_scikit-bio_scipy_mmseqs2:9d5864f776f52aa0' :
        'community.wave.seqera.io/library/python_scikit-bio_scipy_mmseqs2:00f5f2307075f0e0' }"

    input:
    path( ch_kegg_pep_root_dir, stageAs: "kegg_raw" )

    output:
    path( "kegg.pep" ), emit: kegg_pep
    path( "kegg.kff" ), emit: kegg_kff

    script:
    """

    cat "${ch_kegg_pep_root_dir}"/*/*.pep > kegg.pep
    cat "${ch_kegg_pep_root_dir}"/*/*.kff > kegg.kff

    """
}
