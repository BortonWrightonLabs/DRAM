//
// Subworkflow with functionality specific to the BortonWrightonLabs/dram pipeline
//

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT FUNCTIONS / MODULES / SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { UTILS_NFSCHEMA_PLUGIN     } from '../../nf-core/utils_nfschema_plugin'
include { getDBFlag                 } from '../../local/utils_pipeline_setup.nf'
include { paramsSummaryMap          } from 'plugin/nf-schema'
include { samplesheetToList         } from 'plugin/nf-schema'
include { paramsHelp                } from 'plugin/nf-schema'
include { completionEmail           } from '../../nf-core/utils_nfcore_pipeline'
include { completionSummary         } from '../../nf-core/utils_nfcore_pipeline'
include { imNotification            } from '../../nf-core/utils_nfcore_pipeline'
include { UTILS_NFCORE_PIPELINE     } from '../../nf-core/utils_nfcore_pipeline'
include { UTILS_NEXTFLOW_PIPELINE   } from '../../nf-core/utils_nextflow_pipeline'



/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    SUBWORKFLOW TO INITIALISE PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow PIPELINE_INITIALISATION {

    take:
    version           // boolean: Display version and exit
    help              // boolean: Display help text and exit
    validate_params   // boolean: Boolean whether to validate parameters against the schema at runtime
    monochrome_logs   // boolean: Do not use coloured log outputs
    nextflow_cli_args //   array: List of positional nextflow CLI args
    outdir            //  string: The output directory where the results will be saved
    // input             //  string: Path to input samplesheet

    main:

    ch_versions = channel.empty()

    //
    // Print version and exit if required and dump pipeline parameters to JSON file
    //
    UTILS_NEXTFLOW_PIPELINE (
        version,
        true,
        outdir,
        workflow.profile.tokenize(',').intersect(['conda', 'mamba']).size() >= 1
    )


    //
    // Check pipeline params that need to be validated outside of the nf-schema plugin
    //

    use_kegg = params.use_kegg
    use_fegenie = params.use_fegenie
    use_sulfur = params.use_sulfur
    use_pfam = params.use_pfam
    use_kofam = params.use_kofam


    if (params.anno_dbs != "") {
        anno_dbs = params.anno_dbs.tokenize(',').collect { it.trim().toLowerCase() }
        value_for_all = 'all'
        use_kegg = getDBFlag(anno_dbs, 'kegg', value_for_all, params.kegg_db)
        use_kofam = getDBFlag(anno_dbs, 'kofam', value_for_all, params.kofam_db)
        use_fegenie = getDBFlag(anno_dbs, 'fegenie', value_for_all, params.fegenie_db)
        use_sulfur = getDBFlag(anno_dbs, 'sulfur', value_for_all, params.sulfur_db)
        // use_pfam = getDBFlag(anno_dbs, 'pfam', value_for_all)
        // PFAM database is currently disabled in this pipeline due to a bug in the DRAM2 implementation with the PFAM database. It will be re-enabled in a future release.
    }

    if (params.annotate && params.annotations) {
        error("--annotations cannot be used with --annotate. Annotations file is used when you are running without annotate.")
    }

    if (params.summarize && (!params.annotate && !params.annotations)) {
        error("--summarize must be used with --annotate or --annotations.")
    }
    if (params.traits && (!params.annotate && !params.annotations)) {
        error("--traits must be used with --annotate or --annotations.")
    }
    if (params.visualize && (!params.annotate && !params.annotations)) {
        error("--visualize must be used with --annotate or --annotations.")
    }

    if (params.input_genes) {
        if (params.call) {
            error("Input genes file cannot be used with --call. Input genes is used when you are running annotate without call.")
        }
        if (params.input_fasta) {
            error("--input_genes and --input_fasta both specified, please specify only one.")
        }
    }

    if (params.trnas || params.rrnas) {
        if (params.call) {
            error("Input tRNAs and rRNAs files cannot be used with --call. Input tRNAs and rRNAs are used when you are running without call.")
        }
    }

    // if (((params.adjectives || params.traits) || (params.visualize || params.product)) && ((!use_kegg && !use_kofam) || !use_fegenie || !use_sulfur)) {
    //     // If they are using a premade annotations file, we just trust that they used kegg, fegenies, or sulfur
    //     if (!params.annotations) {
    //         error("When using Traits or viz, make sure you use (Kegg or Kofam), FeGenie, and Sulfur Databases")
    //     }
    // }

    if (use_pfam) {
        error("PFAM database is currently disabled in this pipeline due to a bug in the DRAM2 implementation with the PFAM database. It will be re-enabled in a future release.")
    }

    //
    // Validate parameters and generate parameter summary to stdout
    //
    UTILS_NFSCHEMA_PLUGIN (
        workflow,
        validate_params,
        null
    )

    //
    // Check config provided to the pipeline
    //
    UTILS_NFCORE_PIPELINE (
        nextflow_cli_args
    )

    //
    // Create channel from input file provided through params.input
    //

    // Channel
    //     .fromList(samplesheetToList(params.input, "${projectDir}/assets/schema_input.json"))
    //     .map {
    //         meta, fastq_1, fastq_2 ->
    //             if (!fastq_2) {
    //                 return [ meta.id, meta + [ single_end:true ], [ fastq_1 ] ]
    //             } else {
    //                 return [ meta.id, meta + [ single_end:false ], [ fastq_1, fastq_2 ] ]
    //             }
    //     }
    //     .groupTuple()
    //     .map { samplesheet ->
    //         validateInputSamplesheet(samplesheet)
    //     }
    //     .map {
    //         meta, fastqs ->
    //             return [ meta, fastqs.flatten() ]
    //     }
    //     .set { ch_samplesheet }

    emit:
    versions    = ch_versions
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    SUBWORKFLOW FOR PIPELINE COMPLETION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow PIPELINE_COMPLETION {

    take:
    email           //  string: email address
    email_on_fail   //  string: email address sent on pipeline failure
    plaintext_email // boolean: Send plain-text email instead of HTML
    outdir          //    path: Path to output directory where results will be published
    monochrome_logs // boolean: Disable ANSI colour codes in log output
    hook_url        //  string: hook URL for notifications
    multiqc_report  //  string: Path to MultiQC report

    main:
    summary_params = paramsSummaryMap(workflow, parameters_schema: "nextflow_schema.json")
    def multiqc_reports = multiqc_report.toList()

    //
    // Completion email and summary
    //
    workflow.onComplete {
        if (email || email_on_fail) {
            completionEmail(
                summary_params,
                email,
                email_on_fail,
                plaintext_email,
                outdir,
                monochrome_logs,
                multiqc_reports.getVal(),
            )
        }

        completionSummary(monochrome_logs)
        if (hook_url) {
            imNotification(summary_params, hook_url)
        }

        def logFile = file('.nextflow.log')
        if (outdir && logFile.exists()) {
            def newLoc = file(outdir) / "pipeline_info" / ".nextflow.log"
            log.debug("Moving .nextflow.log to: ${newLoc}")
            nextflow.extension.FilesEx.copyTo(logFile, newLoc)
        }


    }

    workflow.onError {
        log.error "Pipeline failed. Please refer to troubleshooting docs: https://nf-co.re/docs/usage/troubleshooting"
    }
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//
// Validate channels from input samplesheet
//
def validateInputSamplesheet(input) {
    def (metas, fastqs) = input[1..2]

    // Check that multiple runs of the same sample are of the same datatype i.e. single-end / paired-end
    def endedness_ok = metas.collect{ meta -> meta.single_end }.unique().size == 1
    if (!endedness_ok) {
        error("Please check input samplesheet -> Multiple runs of a sample must be of the same datatype i.e. single-end or paired-end: ${metas[0].id}")
    }

    return [ metas[0], fastqs ]
}
//
// Generate methods description for MultiQC
//
def toolCitationText() {
    // TODO nf-core: Optionally add in-text citation tools to this list.
    // Can use ternary operators to dynamically construct based conditions, e.g. params["run_xyz"] ? "Tool (Foo et al. 2023)" : "",
    // Uncomment function in methodsDescriptionText to render in MultiQC report
    def citation_text = [
            "Tools used in the workflow included:",
            "MultiQC (Ewels et al. 2016)",
            "."
        ].join(' ').trim()

    return citation_text
}

def toolBibliographyText() {
    // TODO nf-core: Optionally add bibliographic entries to this list.
    // Can use ternary operators to dynamically construct based conditions, e.g. params["run_xyz"] ? "<li>Author (2023) Pub name, Journal, DOI</li>" : "",
    // Uncomment function in methodsDescriptionText to render in MultiQC report
    def reference_text = [
            "<li>Ewels, P., Magnusson, M., Lundin, S., & Käller, M. (2016). MultiQC: summarize analysis results for multiple tools and samples in a single report. Bioinformatics , 32(19), 3047–3048. doi: /10.1093/bioinformatics/btw354</li>"
        ].join(' ').trim()

    return reference_text
}

def methodsDescriptionText(mqc_methods_yaml) {
    // Convert  to a named map so can be used as with familiar NXF ${workflow} variable syntax in the MultiQC YML file
    def meta = [:]
    meta.workflow = workflow.toMap()
    meta["manifest_map"] = workflow.manifest.toMap()

    // Pipeline DOI
    if (meta.manifest_map.doi) {
        // Using a loop to handle multiple DOIs
        // Removing `https://doi.org/` to handle pipelines using DOIs vs DOI resolvers
        // Removing ` ` since the manifest.doi is a string and not a proper list
        def temp_doi_ref = ""
        def manifest_doi = meta.manifest_map.doi.tokenize(",")
        manifest_doi.each { doi_ref ->
            temp_doi_ref += "(doi: <a href=\'https://doi.org/${doi_ref.replace("https://doi.org/", "").replace(" ", "")}\'>${doi_ref.replace("https://doi.org/", "").replace(" ", "")}</a>), "
        }
        meta["doi_text"] = temp_doi_ref.substring(0, temp_doi_ref.length() - 2)
    } else meta["doi_text"] = ""
    meta["nodoi_text"] = meta.manifest_map.doi ? "" : "<li>If available, make sure to update the text to include the Zenodo DOI of version of the pipeline used. </li>"

    // Tool references
    meta["tool_citations"] = ""
    meta["tool_bibliography"] = ""

    // TODO nf-core: Only uncomment below if logic in toolCitationText/toolBibliographyText has been filled!
    // meta["tool_citations"] = toolCitationText().replaceAll(", \\.", ".").replaceAll("\\. \\.", ".").replaceAll(", \\.", ".")
    // meta["tool_bibliography"] = toolBibliographyText()


    def methods_text = mqc_methods_yaml.text

    def engine =  new groovy.text.SimpleTemplateEngine()
    def description_html = engine.createTemplate(methods_text).make(meta)

    return description_html.toString()
}
