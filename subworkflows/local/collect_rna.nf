//
// Subworkflow with functionality specific to the BortonWrightonLabs/dram pipeline
//

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT FUNCTIONS / MODULES / SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { TRNA_SCAN as TRNA_SCAN_SMALL                  } from "../../modules/local/collect_rna/trna_scan.nf"
include { TRNA_SCAN as TRNA_SCAN_MEDIUM                 } from "../../modules/local/collect_rna/trna_scan.nf"
include { TRNA_SCAN as TRNA_SCAN_LARGE                  } from "../../modules/local/collect_rna/trna_scan.nf"
include { RRNA_SCAN as RRNA_SCAN_SMALL                  } from "../../modules/local/collect_rna/rrna_scan.nf"
include { RRNA_SCAN as RRNA_SCAN_MEDIUM                 } from "../../modules/local/collect_rna/rrna_scan.nf"
include { RRNA_SCAN as RRNA_SCAN_LARGE                  } from "../../modules/local/collect_rna/rrna_scan.nf"
include { TRNA_COLLECT                                  } from "../../modules/local/collect_rna/trna_collect.nf"
include { RRNA_COLLECT                                  } from "../../modules/local/collect_rna/rrna_collect.nf"
include {bucketFastaBatches; batchMaxBytes; unpackBatchOutputs } from './utils_batches.nf'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    SUBWORKFLOW TO COLLECT RNA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow COLLECT_RNA {
    take:
    ch_fasta  // channel: [ val(input_fasta name), path(fasta), val(logical bytes) ]
    default_sheet // Path to dummy sheet
    scan_input_fasta // boolean: whether raw FASTA input is available

    main:

    run_rrna_collect = false
    run_trna_collect = false

    if (!scan_input_fasta) {
        if (params.rrnas) {
            channel.fromPath("${params.rrnas}/*.tsv", checkIfExists: true)
                .ifEmpty { exit 1, "Cannot find individual rRNA files generated with barrnap at: ${params.rrnas}\nNB: Path needs to follow pattern: path/to/directory" }
                .collect()
                .set { ch_collected_rRNAs }
                run_rrna_collect = true
        }
        else {
            log.warn("No rRNA files provided, skipping rRNA steps.")
        }
        if (params.trnas) {
            channel.fromPath("${params.trnas}/*.tsv", checkIfExists: true)
                .ifEmpty { exit 1, "Cannot find individual tRNA files generated with tRNAscan-SE. Cannot find any files at: ${params.trnas}\nNB: Path needs to follow pattern: path/to/directory" }
                .collect()
                .set { ch_collected_tRNAs }
                run_trna_collect = true
        }
        else {
            log.warn("No tRNA files provided, skipping tRNA steps.")
        }
    } else {
        ch_fasta_by_resource = bucketFastaBatches(ch_fasta,
            params.rna_batch_size as int,
            batchMaxBytes(params.rna_batch_max_size))

        // Keep the scanners separate so failures, retries, and overrides remain isolated.
        TRNA_SCAN_SMALL(ch_fasta_by_resource.small)
        TRNA_SCAN_MEDIUM(ch_fasta_by_resource.medium)
        TRNA_SCAN_LARGE(ch_fasta_by_resource.large)
        ch_trna_scan = TRNA_SCAN_SMALL.out.trna_scan_out
            .mix(TRNA_SCAN_MEDIUM.out.trna_scan_out, TRNA_SCAN_LARGE.out.trna_scan_out)
            .flatMap { names, files -> unpackBatchOutputs(names, files, '_processed_trnas.tsv') }
        // Collect all input_fasta formatted tRNA files
        channel.empty()
            .mix( ch_trna_scan )
            .collect()
            .set { ch_collected_tRNAs }
        RRNA_SCAN_SMALL(ch_fasta_by_resource.small)
        RRNA_SCAN_MEDIUM(ch_fasta_by_resource.medium)
        RRNA_SCAN_LARGE(ch_fasta_by_resource.large)
        ch_rrna_scan = RRNA_SCAN_SMALL.out.rrna_scan_out
            .mix(RRNA_SCAN_MEDIUM.out.rrna_scan_out, RRNA_SCAN_LARGE.out.rrna_scan_out)
            .flatMap { names, files -> unpackBatchOutputs(names, files, '_processed_rrnas.tsv') }
        channel.empty()
            .mix( ch_rrna_scan )
            .collect()
            .set { ch_collected_rRNAs }
        run_rrna_collect = true
        run_trna_collect = true
    }

    ch_rrna_collected = default_sheet
    ch_rrna_combined = default_sheet
    if (run_rrna_collect) {
        // Create sheet for rrnas from the collected rRNAs or provided rRNAs
        // Run RRNA_COLLECT to generate a combined TSV for all fastas
        RRNA_COLLECT( ch_collected_rRNAs )
        ch_rrna_collected = RRNA_COLLECT.out.rrna_collected_out.ifEmpty(default_sheet)
        ch_rrna_combined = RRNA_COLLECT.out.rrna_combined_out.ifEmpty(default_sheet)
    }
    ch_trna_collected = default_sheet
    ch_trna_combined = default_sheet
    if (run_trna_collect) {
        // Create sheet for trnas from the collected tRNAs or provided tRNAs
        // Run TRNA_COLLECT to generate a combined TSV for all fastas
        TRNA_COLLECT( ch_collected_tRNAs )
        ch_trna_collected = TRNA_COLLECT.out.trna_collected_out.ifEmpty(default_sheet)
        ch_trna_combined = TRNA_COLLECT.out.trna_combined_out.ifEmpty(default_sheet)
    }

    emit:
    ch_rrna_collected
    ch_rrna_combined
    ch_trna_collected
    ch_trna_combined

}
