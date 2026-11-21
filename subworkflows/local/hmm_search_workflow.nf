include { HMM_SEARCH as SEARCH_SMALL; HMM_SEARCH as SEARCH_MEDIUM; HMM_SEARCH as SEARCH_LARGE } from '../../modules/local/annotate/hmmsearch.nf'
include { bucketSearchBatches; unpackBatchOutputs; batchMaxBytes } from './utils_batches.nf'
include { searchTarget } from './utils_resource_classes.nf'

workflow HMM_SEARCH_WORKFLOW {
    take:
    queries
    e_value
    database
    hmm_info
    ec_from_info
    db_name

    main:
    buckets = bucketSearchBatches(queries,
        params.search_batch_size as int,
        batchMaxBytes(params.search_batch_max_size))
    target = database.map { searchTarget(it) }

    SEARCH_SMALL(buckets.small.combine(target), e_value, database, hmm_info, ec_from_info, db_name)
    SEARCH_MEDIUM(buckets.medium.combine(target), e_value, database, hmm_info, ec_from_info, db_name)
    SEARCH_LARGE(buckets.large.combine(target), e_value, database, hmm_info, ec_from_info, db_name)

    formatted = SEARCH_SMALL.out.formatted_hits
        .mix(SEARCH_MEDIUM.out.formatted_hits, SEARCH_LARGE.out.formatted_hits)
        .flatMap { names, files -> unpackBatchOutputs(names, files, "___formatted_${db_name}_hits.csv") }

    emit:
    formatted_hits = formatted
}
