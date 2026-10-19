process FORMAT_KEGG_DB {
    label 'process_huge'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_scikit-bio_scipy_mmseqs2:9d5864f776f52aa0' :
        'community.wave.seqera.io/library/python_scikit-bio_scipy_mmseqs2:00f5f2307075f0e0' }"

    tag { ch_kegg_pep }

    input:
        path( ch_kegg_pep, stageAs: "kegg_pep_loc" )
        path(gene_ko_link_loc)
        val(kegg_download_date)
        val(skip_gene_ko_link)

    output:
        path( "kegg/*" )

    script:
    """
    if [ "${skip_gene_ko_link}" = "true" ]; then
        echo "No Gene KO Link file provided. Running KEGG DB formatting without"
        format_kegg_database.py --kegg_loc ${ch_kegg_pep} --download_date ${kegg_download_date} --threads ${params.threads} --output_dir kegg --skip_gene_ko_link
    else
        echo "Gene KO Link file provided. Running KEGG DB formatting with Gene KO Link file"
        format_kegg_database.py --kegg_loc ${ch_kegg_pep} --gene_ko_link_loc ${gene_ko_link_loc} --download_date ${kegg_download_date} --threads ${params.threads} --output_dir kegg
    fi

    """
}
