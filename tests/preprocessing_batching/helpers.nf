include { packFastaBatches; unpackBatchOutputs } from '../../subworkflows/local/utils_batches.nf'
include { resourceClass } from '../../subworkflows/local/utils_resource_classes.nf'

workflow {
    def mib = 1024L * 1024L
    def gib = 1024L * 1024L * 1024L
    def record = { name, bytes -> [name, file("/tmp/${name}.fa"), bytes] }

    assert [200 * mib, 200 * mib + 1, gib, gib + 1].collect { resourceClass(it) } ==
        ['small', 'medium', 'medium', 'large']

    def records = [record('c', 4L), record('a', 4L), record('b', 4L)]
    def batches = packFastaBatches(records, 2, 8L)
    assert batches.collect { it[1] } == [['a', 'b'], ['c']]
    assert packFastaBatches(records.reverse(), 2, 8L) == batches
    assert packFastaBatches(records, 10, 3L).every { it[1].size() == 1 }
    assert packFastaBatches([record('a', 8L), record('b', 1L)], 10, 8L)*.getAt(1) == [['a', 'b']]
    assert packFastaBatches([record('a', 9L), record('b', 1L)], 10, 8L)*.getAt(1) == [['b'], ['a']]
    assert packFastaBatches([], 10, 8L) == []
    assert packFastaBatches([record('a', 150 * mib), record('b', 150 * mib)], 2, gib)[0][0] == 'small'

    def mixed = packFastaBatches([record('a', 1L), record('b', 20 * gib + 1)], 10, 100 * gib)
    assert mixed.size() == 1
    assert mixed[0][0] == 'large'

    if (params.duplicate_test) {
        packFastaBatches([record('a', 1L), record('a', 2L)], 2, gib)
    }

    assert unpackBatchOutputs(['a', 'b'], file('/tmp/b_called_genes.faa'), '_called_genes.faa') ==
        [tuple('b', file('/tmp/b_called_genes.faa'))]
    println 'Preprocessing batch helper assertions passed'
}
