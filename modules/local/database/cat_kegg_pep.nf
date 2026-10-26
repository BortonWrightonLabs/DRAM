process CAT_KEGG_PEP {

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
