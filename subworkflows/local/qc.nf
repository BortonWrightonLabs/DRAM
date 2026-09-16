include { COLLECT_RNA            } from "../../subworkflows/local/collect_rna.nf"
include { ADD_TAXA               } from "../../modules/local/add_and_combine/add_taxa.nf"
include { ADD_BIN_QUALITY        } from "../../modules/local/add_and_combine/add_bin_quality.nf"

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    SUBWORKFLOW TO QC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow QC {
    take:
    ch_fasta  // channel: [ val(input_fasta name), path(fasta), val(logical bytes) ]
    default_sheet // Path to dummy sheet
    ch_combined_annotations  // channel: [ path(combined_annotations_out) ]
    scan_input_fasta         // boolean: whether raw FASTA input is available

    main:

    COLLECT_RNA( ch_fasta, default_sheet, scan_input_fasta )
    ch_rrna_collected = COLLECT_RNA.out.ch_rrna_collected
    ch_trna_collected = COLLECT_RNA.out.ch_trna_collected
    ch_trna_combined = COLLECT_RNA.out.ch_trna_combined


    // Add Bin Quality to annotations
    if( params.bin_quality ){
        ch_bin_quality = file(params.bin_quality)
        ADD_BIN_QUALITY( ch_combined_annotations, ch_bin_quality )
        ch_updated_annots = ADD_BIN_QUALITY.out.annots_bin_quality_out
    }
    else{
        ch_updated_annots = ch_combined_annotations
    }

    // Add Taxonomy to annotations
    if( params.taxa ){
        ch_taxa = file(params.taxa)
        ADD_TAXA( ch_updated_annots, ch_taxa )
        ch_updated_taxa_annots = ADD_TAXA.out.annots_taxa_out
    }
    else{
        ch_updated_taxa_annots = ch_updated_annots
    }

    ch_final_annots = ch_updated_taxa_annots

    emit:
    ch_final_annots
    ch_rrna_collected
    ch_trna_collected
    ch_trna_combined
}
