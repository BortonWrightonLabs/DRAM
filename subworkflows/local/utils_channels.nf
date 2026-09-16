def batchManifestToTuples(ch_renamed_batch) {
    ch_renamed_batch.flatMap { manifest, renamed_files ->
        def files = renamed_files instanceof List ? renamed_files : [renamed_files]
        def files_by_name = files.collectEntries { renamed_file ->
            [(renamed_file.getFileName().toString()): renamed_file]
        }

        manifest.readLines()
            .findAll { line -> line }
            .collect { line ->
                def (name, relpath) = line.split('\t')
                def renamed_file = files_by_name[relpath]
                if (!renamed_file) {
                    error("Could not find renamed file `${relpath}` listed in ${manifest}")
                }
                tuple(name, renamed_file)
            }
    }
}

def collectNamePathTuples(ch_name_path, check_size = false) {
    ch_name_path
        .collect(flat: false)
        .map { rows ->
            def names = rows.collect { tup -> tup[0] }
            def paths = rows.collect { tup -> tup[1] }
            tuple(names, paths)
        }
        .filter { names, _paths -> !check_size || names.size() > 0 }
}
