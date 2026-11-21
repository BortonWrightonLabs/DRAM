include { MMSEQS_SEARCH as SEARCH_SMALL; MMSEQS_SEARCH as SEARCH_MEDIUM; MMSEQS_SEARCH as SEARCH_LARGE } from '../../modules/local/annotate/mmseqs_search.nf'
include { MMSEQS_SEARCH_GPU as SEARCH_GPU_SMALL; MMSEQS_SEARCH_GPU as SEARCH_GPU_MEDIUM; MMSEQS_SEARCH_GPU as SEARCH_GPU_LARGE } from '../../modules/local/annotate/mmseqs_search_gpu.nf'
include { bucketSearchBatches; unpackBatchOutputs; batchMaxBytes } from './utils_batches.nf'
include { searchTarget } from './utils_resource_classes.nf'

workflow MMSEQS_SEARCH_WORKFLOW {
    take:
    queries
    database
    bit_score_threshold
    rbh_bit_score_threshold
    descriptions
    db_name
    sensitivity_rounds  // boolean: search in sensitivity rounds

    main:
    buckets = bucketSearchBatches(queries,
        params.search_batch_size as int,
        batchMaxBytes(params.search_batch_max_size))
    target = database.map { searchTarget(it) }

    SEARCH_SMALL(buckets.small.combine(target), database, bit_score_threshold, rbh_bit_score_threshold, descriptions, db_name, sensitivity_rounds)
    SEARCH_MEDIUM(buckets.medium.combine(target), database, bit_score_threshold, rbh_bit_score_threshold, descriptions, db_name, sensitivity_rounds)
    SEARCH_LARGE(buckets.large.combine(target), database, bit_score_threshold, rbh_bit_score_threshold, descriptions, db_name, sensitivity_rounds)

    raw = SEARCH_SMALL.out.mmseqs_search_raw_out
        .mix(SEARCH_MEDIUM.out.mmseqs_search_raw_out, SEARCH_LARGE.out.mmseqs_search_raw_out)
        .flatMap { names, files -> unpackBatchOutputs(names, files, "___mmseqs_${db_name}.tsv") }
    formatted = SEARCH_SMALL.out.mmseqs_search_formatted_out
        .mix(SEARCH_MEDIUM.out.mmseqs_search_formatted_out, SEARCH_LARGE.out.mmseqs_search_formatted_out)
        .flatMap { names, files -> unpackBatchOutputs(names, files, "___mmseqs_${db_name}_formatted.csv") }

    emit:
    mmseqs_search_raw_out = raw
    mmseqs_search_formatted_out = formatted
}

workflow MMSEQS_SEARCH_GPU_WORKFLOW {
    take:
    queries
    database
    bit_score_threshold
    rbh_bit_score_threshold
    descriptions
    db_name

    main:
    buckets = bucketSearchBatches(queries,
        params.search_batch_size as int,
        batchMaxBytes(params.search_batch_max_size))
    target = database.map { searchTarget(it) }

    SEARCH_GPU_SMALL(buckets.small.combine(target), database, bit_score_threshold, rbh_bit_score_threshold, descriptions, db_name)
    SEARCH_GPU_MEDIUM(buckets.medium.combine(target), database, bit_score_threshold, rbh_bit_score_threshold, descriptions, db_name)
    SEARCH_GPU_LARGE(buckets.large.combine(target), database, bit_score_threshold, rbh_bit_score_threshold, descriptions, db_name)

    raw = SEARCH_GPU_SMALL.out.mmseqs_search_raw_out
        .mix(SEARCH_GPU_MEDIUM.out.mmseqs_search_raw_out, SEARCH_GPU_LARGE.out.mmseqs_search_raw_out)
        .flatMap { names, files -> unpackBatchOutputs(names, files, "___mmseqs_${db_name}.tsv") }
    formatted = SEARCH_GPU_SMALL.out.mmseqs_search_formatted_out
        .mix(SEARCH_GPU_MEDIUM.out.mmseqs_search_formatted_out, SEARCH_GPU_LARGE.out.mmseqs_search_formatted_out)
        .flatMap { names, files -> unpackBatchOutputs(names, files, "___mmseqs_${db_name}_formatted.csv") }

    emit:
    mmseqs_search_raw_out = raw
    mmseqs_search_formatted_out = formatted
}
