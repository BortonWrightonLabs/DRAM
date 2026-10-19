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
