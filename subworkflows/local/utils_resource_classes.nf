/*
 * Return the total number of bytes represented by a path, directory, or nested
 * collection of paths. Directory contents are summed recursively.
 */
def resourceBytes(value) {
    if (value == null) {
        return 0L
    }
    if (value instanceof Map) {
        return value.values().collect { resourceBytes(it) }.sum(0L) as long
    }
    if (value instanceof Collection) {
        return value.collect { resourceBytes(it) }.sum(0L) as long
    }
    if (value.getClass().isArray()) {
        return value.collect { resourceBytes(it) }.sum(0L) as long
    }
    if (value.isFile()) {
        return value.size() as long
    }
    if (value.isDirectory()) {
        def bytes = 0L
        value.eachFileRecurse { entry ->
            if (entry.isFile()) {
                bytes += entry.size() as long
            }
        }
        return bytes
    }

    throw new IllegalArgumentException(
        "Cannot calculate resource size for ${value.getClass().name}"
    )
}

def resourceClass(bytes) {
    def thresholds = [params.resource_class_small_max_size, params.resource_class_medium_max_size].collect { value ->
        def normalized = value.toString().replaceFirst(/\.(?=\s*[KMGT]?B$)/, '')
        nextflow.util.MemoryUnit.of(normalized).toBytes()
    }
    def (small_max_bytes, medium_max_bytes) = thresholds

    if (small_max_bytes < 1 || medium_max_bytes <= small_max_bytes) {
        throw new IllegalArgumentException(
            'Resource class thresholds must be positive, with resource_class_small_max_size < resource_class_medium_max_size'
        )
    }

    if (bytes <= small_max_bytes) {
        return 'small'
    }
    if (bytes <= medium_max_bytes) {
        return 'medium'
    }
    return 'large'
}

/*
 * Size of a search target, for sizing search tasks by database rather than
 * only by genome. `bytes` is what the search has to hold: an MMseqs2
 * database's `.idx` when it has one (MMseqs2 maps the whole index), otherwise
 * the whole database. `small` marks databases whose searches take seconds, so
 * extra CPUs would only sit reserved.
 */
def searchTarget(database) {
    def index = database.isDirectory()
        ? database.listFiles().findAll { it.isFile() && it.name.endsWith('.idx') }.max { it.size() }
        : null
    def bytes = index ? index.size() as long : resourceBytes(database)
    // 4 GiB separates the seconds-long searches (MEROPS index 3.1 GiB, the HMM
    // sets under 100 MiB) from KOfam, VOG, Pfam, KEGG and UniRef.
    return [bytes: bytes, small: bytes < 4L * 1024L * 1024L * 1024L]
}
