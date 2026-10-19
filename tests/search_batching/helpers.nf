include { packSearchBatches; unpackBatchOutputs } from '../../subworkflows/local/utils_batches.nf'
include { resourceClass } from '../../subworkflows/local/utils_resource_classes.nf'

workflow {
    def mib = 1024L * 1024L
    def gib = 1024L * 1024L * 1024L
    def record = { name, bytes -> [name, file("/tmp/${name}.faa"), file("/tmp/${name}.tsv"), bytes] }
    assert [200 * mib, 200 * mib + 1, gib, gib + 1].collect { resourceClass(it) } == ['small', 'medium', 'medium', 'large']
    def records = [record('c', 4L), record('a', 4L), record('b', 4L)]
    def batches = packSearchBatches(records, 2, 8L)
    assert batches.collect { it[1] } == [['a', 'b'], ['c']]
    assert packSearchBatches(records.reverse(), 2, 8L) == batches
    assert packSearchBatches(records, 10, 3L).every { it[1].size() == 1 }
    assert packSearchBatches([record('a', 8L), record('b', 1L)], 10, 8L)*.getAt(1) == [['a', 'b']]
    assert packSearchBatches([record('a', 9L), record('b', 1L)], 10, 8L)*.getAt(1) == [['b'], ['a']]
    assert packSearchBatches([], 10, 8L) == []
    // Resource class uses the largest individual query, not the batch total.
    assert packSearchBatches([record('a', 150 * mib), record('b', 150 * mib)], 2, gib)[0][0] == 'small'
    // Inputs below the threshold can share a batch even when their classes differ.
    def mixed = packSearchBatches([record('a', 1L), record('b', 20 * gib + 1)], 10, 100 * gib)
    assert mixed.size() == 1
    assert mixed[0][0] == 'large'
    if (params.duplicate_test) {
        packSearchBatches([record('a', 1L), record('a', 2L)], 2, gib)
    }
    assert unpackBatchOutputs(['a', 'b'], file('/tmp/b___hits.csv'), '___hits.csv') == [tuple('b', file('/tmp/b___hits.csv'))]
    assert unpackBatchOutputs(['a___b', 'a'], [file('/tmp/a___b___hits.csv')], '___hits.csv')*.getAt(0) == ['a___b']
    println 'Search batch helper assertions passed'
}
