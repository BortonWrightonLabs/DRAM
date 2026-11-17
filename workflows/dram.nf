/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { MULTIQC                 } from '../modules/nf-core/multiqc/main'
include { paramsSummaryMap        } from 'plugin/nf-schema'
include { paramsSummaryMultiqc    } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { softwareVersionsToYAML  } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { methodsDescriptionText  } from '../subworkflows/local/utils_nfcore_dram_pipeline'
include { getDBFlag               } from '../subworkflows/local/utils_pipeline_setup.nf'

// Pipeline steps
include { REFINE                 } from "../modules/local/refine/refine.nf"
include { CAT_KEGG_PEP           } from "../modules/local/database/cat_kegg_pep.nf"
include { FORMAT_KEGG_DB         } from "../modules/local/database/format_kegg_db.nf"
include { MMSEQS_GPU_DATABASE    } from "../modules/local/database/mmseqs_gpu_database.nf"
include { MERGE                  } from "../subworkflows/local/merge.nf"
include { ANNOTATE               } from "../subworkflows/local/annotate.nf"
include { QC                     } from "../subworkflows/local/qc.nf"
include { ADD_ANNOTATIONS        } from "../modules/local/add_and_combine/add_annotations.nf"
include { DECOMPRESS_FASTA       } from "../modules/local/rename/decompress_fasta.nf"
include { RENAME_FASTA           } from "../modules/local/rename/rename_fasta.nf"
include { resourceBytes          } from '../subworkflows/local/utils_resource_classes.nf'
include { batchManifestToTuples; collectNamePathTuples } from '../subworkflows/local/utils_channels.nf'


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow DRAM {

    main:

    //
    // Setup
    //

    ch_versions = channel.empty()
    ch_multiqc_files = channel.empty()
    ch_fasta = channel.empty()

    default_sheet = file(params.distill_dummy_sheet)

    // Deprecated params: warn, and return the first one given
    def deprecated = { List names, String now ->
        def given = names.findAll { params[it] }
        given.each { log.warn("--${it} is deprecated; use --${now}") }
        given ? params[given[0]] : null
    }
    // The old Summarize params turned on Summarize on their own, so they still do
    summarize = params.refine || params.summarize || params.sum_custom ||
        ['sum_topics', 'sum_ecos', 'distill_topic', 'distill_ecosystem', 'distill_custom'].any { params[it] }
    visualize = params.refine || params.visualize || deprecated(['product'], 'visualize')
    traits = params.refine || params.traits || deprecated(['adjectives'], 'traits')

    // if annotate with raw fasta but no call, we can infer we need to call genes, so set call to true
    // Also, if call is specified, set call to true
    call = false
    if ((params.annotate && params.input_fasta) || params.call) {
        call = true
    }

    if (params.input_fasta && (params.rename || call || params.qc)) {
        ch_fasta_raw = channel
            .fromPath(file(params.input_fasta) / params.fasta_fmt, checkIfExists: true)
                .ifEmpty { exit 1, "Cannot find any fasta files matching: ${params.input_fasta}\nNB: Path needs to follow pattern: path/to/directory/" }

        // Strip .gz (if present) and then .fa/.fna/.fasta so a sample's
        // gz and plain inputs yield the same downstream sample name.
        ch_fasta_named = ch_fasta_raw.map { f ->
            def name = f.name.replaceAll(/\.gz$/, '').replaceAll(/\.(fa|fna|fasta)$/, '')
            tuple(name, f)
        }

        // Route .gz inputs through DECOMPRESS_FASTA; pass plain inputs unchanged.
        ch_fasta_branched = ch_fasta_named.branch { entry ->
            gz: entry[1].name.endsWith('.gz')
            plain: true
        }

        DECOMPRESS_FASTA( ch_fasta_branched.gz )
        ch_fasta = DECOMPRESS_FASTA.out.decompressed_fasta.mix( ch_fasta_branched.plain )

        if (params.rename) {
            ch_fasta_collected = collectNamePathTuples(ch_fasta)
            RENAME_FASTA( ch_fasta_collected )
            ch_fasta = batchManifestToTuples(RENAME_FASTA.out.renamed_batch)
        }

        ch_fasta = ch_fasta.map { name, fasta -> tuple(name, fasta, resourceBytes(fasta)) }
    }
    use_kegg = params.use_kegg
    use_kofam = params.use_kofam
    use_dbcan = params.use_dbcan
    use_camper = params.use_camper
    use_fegenie = params.use_fegenie
    use_methyl = params.use_methyl
    use_canthyd = params.use_canthyd
    use_sulfur = params.use_sulfur
    use_pfam = params.use_pfam
    use_merops = params.use_merops
    use_uniref = params.use_uniref
    use_metals = params.use_metals
    use_antismash = params.use_antismash
    use_rgi = params.use_rgi
    use_card = params.use_card
    use_tcdb = params.use_tcdb
    use_dram_db = params.use_dram_db
    use_vog = params.use_vog
    if (params.anno_dbs != "") {
        anno_dbs = params.anno_dbs.tokenize(',').collect { it.trim().toLowerCase() }
        value_for_all = 'all'
        use_kegg = getDBFlag(anno_dbs, 'kegg', value_for_all, params.kegg_db)
        use_kofam = getDBFlag(anno_dbs, 'kofam', value_for_all, params.kofam_db)
        use_dbcan = getDBFlag(anno_dbs, 'dbcan', value_for_all, params.dbcan_db)
        use_camper = getDBFlag(anno_dbs, 'camper', value_for_all, params.camper_hmm_db)
        use_fegenie = getDBFlag(anno_dbs, 'fegenie', value_for_all, params.fegenie_db)
        use_methyl = getDBFlag(anno_dbs, 'methyl', value_for_all, params.methyl_db)
        use_canthyd = getDBFlag(anno_dbs, 'canthyd', value_for_all, params.canthyd_hmm_db)
        use_sulfur = getDBFlag(anno_dbs, 'sulfur', value_for_all, params.sulfur_db)
        // use_pfam = getDBFlag(anno_dbs, 'pfam', value_for_all)
        // PFAM database is currently disabled in this pipeline due to a bug in the DRAM2 implementation with the PFAM database. It will be re-enabled in a future release.
        use_merops = getDBFlag(anno_dbs, 'merops', value_for_all, params.merops_db)
        use_uniref = getDBFlag(anno_dbs, 'uniref', value_for_all, params.uniref_db)
        use_metals = getDBFlag(anno_dbs, 'metals', value_for_all, params.metals_db)
        use_antismash = getDBFlag(anno_dbs, 'antismash', value_for_all, params.antismash_db)
        use_rgi = getDBFlag(anno_dbs, 'rgi', value_for_all, params.card_db)
        use_card = getDBFlag(anno_dbs, 'card', value_for_all, params.card_db)
        use_tcdb = getDBFlag(anno_dbs, 'tcdb', value_for_all, params.tcdb_db)
        use_dram_db = getDBFlag(anno_dbs, 'dram_db', value_for_all, params.dram_db)
        use_vog = getDBFlag(anno_dbs, 'vog', value_for_all, params.vog_db)
    }



    if (summarize && !use_kegg && !use_kofam && !use_dbcan && !use_merops && !params.annotations) {
        error("Error: If you are using summarize, you must also use --use_kegg, --use_kofam, --use_dbcan, or --use_merops.")
    }



    //
    // Collate and save software versions
    //

    softwareVersionsToYAML(ch_versions)
        .collectFile(
            storeDir: "${params.outdir}/pipeline_info",
            name:  'dram_software_'  + 'mqc_'  + 'versions.yml',
            sort: true,
            newLine: true
        ).set { ch_collated_versions }

    //
    // Single step commands
    //

    if (params.format_mmseqs_gpu) {
        if (!params.mmseqs_db_path) {
            error("--mmseqs_db_path is required with --format_mmseqs_gpu.")
        }
        if (!params.mmseqs_db_name) {
            error("--mmseqs_db_name is required with --format_mmseqs_gpu.")
        }
        if (!(params.mmseqs_db_name ==~ /[A-Za-z0-9._-]+/)) {
            error("--mmseqs_db_name may contain only letters, numbers, periods, underscores, and hyphens.")
        }

        mmseqs_db_f = file(params.mmseqs_db_path)
        if (!mmseqs_db_f.exists()) {
            error("MMseqs database directory not found at ${params.mmseqs_db_path}.")
        }

        MMSEQS_GPU_DATABASE(mmseqs_db_f, params.mmseqs_db_name)

    } else if (params.format_kegg){
        if ( params.kegg_pep_root_dir ) {
            CAT_KEGG_PEP( file(params.kegg_pep_root_dir, checkIfExists: true) )
            kegg_pep_f = CAT_KEGG_PEP.out.kegg_pep
            kegg_kff_f = CAT_KEGG_PEP.out.kegg_kff
        }
        else {
            if (!params.kegg_pep_loc || !params.kegg_kff_loc) {
                error("--format_kegg requires --kegg_pep_root_dir containing organism .pep and .kff files, or both --kegg_pep_loc and --kegg_kff_loc.")
            }
            kegg_pep_f = file(params.kegg_pep_loc, checkIfExists: true)
            kegg_kff_f = file(params.kegg_kff_loc, checkIfExists: true)
        }

        kegg_download_date = params.kegg_download_date ?: ""
        FORMAT_KEGG_DB( kegg_pep_f, kegg_kff_f, kegg_download_date )

    } else if (params.merge_annotations){
        MERGE()
    } else {


        //
        // Pipeline steps
        //

        if (params.annotate || params.call) {

            ANNOTATE (
                ch_fasta,
                default_sheet,
                call,
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
                use_vog
            )
        }

        if (params.annotate){ // If the user has specified --annotate, use the outputted annotations
            ch_final_annots = ANNOTATE.out.ch_combined_annotations
        } else if (params.annotations) {
            ch_final_annots = channel
                .fromPath(params.annotations, checkIfExists: true)
                .ifEmpty { exit 1, "Parameter annotations problem: Cannot find any called gene files matching: ${params.annotations}\nNB: Path needs to follow pattern: path/to/directory/" }
        } else {
            ch_final_annots = default_sheet
        }

        ch_trna_combined = default_sheet
        if (params.qc) {
            scan_input_fasta = params.input_fasta ? true : false
            QC( ch_fasta, default_sheet, ch_final_annots, scan_input_fasta )
            ch_final_annots = QC.out.ch_final_annots
            ch_trna_combined = QC.out.ch_trna_combined
        }

        if (params.annotate && params.add_annotations) {
            ch_add_annots = file(params.add_annotations)
            ADD_ANNOTATIONS( ch_final_annots, ch_add_annots )
            ch_final_annots = ADD_ANNOTATIONS.out.combined_annots_out
        }

        if (summarize || visualize || traits) {
            // Old --sum_ecos and --viz_rules_system both become dram-rules' shared --ecos
            def old_ecos = ['sum_ecos', 'distill_ecosystem', 'viz_rules_system'].findAll { params[it] }
            old_ecos.each { log.warn("--${it} is deprecated; use --ecos") }
            def ecos = params.ecos ?: old_ecos.collectMany { params[it].tokenize(',') }.unique().join(',')
            def topics = params.topics ?: deprecated(['sum_topics', 'distill_topic'], 'topics')
            def options = [
                summarize ? '--summarize' : '',
                visualize ? '--visualize' : '',
                traits ? '--traits' : '',
                ecos ? "--ecos ${ecos}" : '',
                topics ? "--topics ${topics}" : '',
            ].findAll().join(' ')
            // Optional files: an empty list when not given
            def files = { value -> value ? value.tokenize(',').collect { file(it, checkIfExists: true) } : [] }
            REFINE(
                ch_final_annots,
                ch_trna_combined,
                options,
                files(params.viz_custom ?: deprecated(['viz_rules_tsv'], 'viz_custom')),
                files(params.traits_custom ?: deprecated(['trait_rules_tsv'], 'traits_custom')),
                files(params.sum_custom ?: deprecated(['distill_custom'], 'sum_custom')),
                files(params.mapping ?: deprecated(['viz_mapping_file'], 'mapping')),
                files(params.common_rules_tsv ?: deprecated(['viz_common_rules_tsv', 'trait_common_rules_tsv'], 'common_rules_tsv')),
            )
        }
    }

    //
    // MODULE: MultiQC
    //
    ch_multiqc_config        = channel.fromPath(
        "$projectDir/assets/multiqc_config.yml", checkIfExists: true)
    ch_multiqc_custom_config = params.multiqc_config ?
        channel.fromPath(params.multiqc_config, checkIfExists: true) :
        channel.empty()
    ch_multiqc_logo          = params.multiqc_logo ?
        channel.fromPath(params.multiqc_logo, checkIfExists: true) :
        channel.empty()

    summary_params      = paramsSummaryMap(
        workflow, parameters_schema: "nextflow_schema.json")
    ch_workflow_summary = channel.value(paramsSummaryMultiqc(summary_params))
    ch_multiqc_files = ch_multiqc_files.mix(
        ch_workflow_summary.collectFile(name: 'workflow_summary_mqc.yaml'))
    ch_multiqc_custom_methods_description = params.multiqc_methods_description ?
        file(params.multiqc_methods_description, checkIfExists: true) :
        file("$projectDir/assets/methods_description_template.yml", checkIfExists: true)
    ch_methods_description                = channel.value(
        methodsDescriptionText(ch_multiqc_custom_methods_description))

    ch_multiqc_files = ch_multiqc_files.mix(ch_collated_versions)
    ch_multiqc_files = ch_multiqc_files.mix(
        ch_methods_description.collectFile(
            name: 'methods_description_mqc.yaml',
            sort: true
        )
    )

    MULTIQC (
        ch_multiqc_files.collect(),
        ch_multiqc_config.toList(),
        ch_multiqc_custom_config.toList(),
        ch_multiqc_logo.toList(),
        [],
        []
    )

    emit:
    multiqc_report = MULTIQC.out.report.toList() // channel: /path/to/multiqc_report.html
    versions       = ch_versions                 // channel: [ path(versions.yml) ]

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
