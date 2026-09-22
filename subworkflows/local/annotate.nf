include { RENAME_PROTEINS        } from "../../modules/local/rename/rename_proteins.nf"
include { RENAME_PROTEINS as RENAME_FNA       } from "../../modules/local/rename/rename_proteins.nf"
include { CALL                   } from "../../subworkflows/local/call.nf"
include { DB_SEARCH              } from "../../subworkflows/local/db_search.nf"
include { GENE_LOCS              } from "../../modules/local/annotate/gene_locs.nf"
include { GENERATE_GFF  } from "../../modules/local/add_and_combine/generate_gff.nf"
include { resourceBytes } from './utils_resource_classes.nf'
include { batchManifestToTuples; collectNamePathTuples } from './utils_channels.nf'
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    SUBWORKFLOW TO ANNOTATE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow ANNOTATE {
    take:
    ch_fasta  // channel: [ val(input_fasta name), path(fasta), val(logical bytes) ]
    default_sheet // Path to dummy sheet
    call     // boolean: whether gene calling flag is set
    use_kegg
    use_kofam
    use_dbcan
    use_camper
    use_fegenie
    use_methyl
    use_canthyd
    use_sulfur
    use_pfam
    use_merops
    use_uniref
    use_metals
    use_antismash
    use_rgi
    use_card
    use_tcdb
    use_dram_db
    use_vog

    main:
    // n_fastas = 0
    ch_combined_annotations = default_sheet

    ch_quast_stats = default_sheet
    ch_gene_gff = channel.empty()
    ch_filtered_fasta = channel.empty()
    ch_called_genes = channel.empty()

    if (call){
        CALL( ch_fasta )
        ch_quast_stats = CALL.out.ch_quast_stats
        ch_gene_locs = CALL.out.ch_gene_locs
        ch_called_proteins = CALL.out.ch_called_proteins
        ch_gene_gff = CALL.out.ch_gene_gff
        ch_filtered_fasta = CALL.out.ch_filtered_fasta
        ch_called_genes = CALL.out.ch_called_genes

    }
    else {
        ch_called_proteins = channel
            .fromPath(file(params.input_genes) / params.genes_fmt, checkIfExists: true)
            .ifEmpty { exit 1, "If you specify --annotate without --call, you must provide a fasta file of called genes using --input_genes. Cannot find any called gene fasta files matching: ${params.input_genes}\n Path needs to follow pattern: path/to/directory/" }
            .map { file ->
                def input_fastaName = file.getBaseName()
                tuple(input_fastaName, file)
            }

        ch_called_genes = channel
            .fromPath(file(params.input_genes) / params.genes_fna_fmt)
            .map { file ->
                def input_fastaName = file.getBaseName()
                tuple(input_fastaName, file)
            }

        ch_called_genes.ifEmpty{ log.warn("No genes matching `genes_fna_fmt` found. Skipping all processes needing called_genes/fna files") }

        if(params.rename) {

            def ch_called_proteins_collected = collectNamePathTuples(ch_called_proteins)
            RENAME_PROTEINS( ch_called_proteins_collected )
            ch_called_proteins = batchManifestToTuples(RENAME_PROTEINS.out.renamed_batch)

            def ch_called_genes_collected = collectNamePathTuples(ch_called_genes, true)
            RENAME_FNA( ch_called_genes_collected )
            ch_called_genes = batchManifestToTuples(RENAME_FNA.out.renamed_batch)
        }

        // input_genes is the final logical query for all downstream searches.
        ch_called_proteins = ch_called_proteins
            .map { name, proteins -> tuple(name, proteins, resourceBytes(proteins)) }

        GENE_LOCS( ch_called_proteins.map { name, proteins, _bytes -> tuple(name, proteins) })
        ch_gene_locs = GENE_LOCS.out.prodigal_locs_tsv

        // n_fastas = file("$params.input_genes/${params.genes_fmt}").size()

    }

    if (params.annotate){
        DB_SEARCH(
            ch_gene_locs,
            ch_called_proteins,
            ch_filtered_fasta,
            ch_gene_gff,
            ch_called_genes,
            default_sheet,
            use_kegg,
            use_kofam,
            use_dbcan,
            use_camper,
            use_fegenie,
            use_methyl,
            use_canthyd,
            use_sulfur,
            use_pfam,
            use_merops,
            use_uniref,
            use_metals,
            use_antismash,
            use_rgi,
            use_card,
            use_tcdb,
            use_dram_db,
            use_vog,
            call
            )
        ch_combined_annotations = DB_SEARCH.out.ch_combined_annotations
    }

    emit:
    ch_combined_annotations
    ch_quast_stats

}
