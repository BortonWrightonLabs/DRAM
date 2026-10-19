process MMSEQS_GPU_DATABASE {
    label 'process_huge'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_scikit-bio_scipy_mmseqs2:9d5864f776f52aa0' :
        'community.wave.seqera.io/library/python_scikit-bio_scipy_mmseqs2:00f5f2307075f0e0' }"

    tag { db_name }

    input:
    path( mmseqs_database )
    val( db_name )

    output:
    path( "${db_name}_gpu" ), emit: gpu_mmseqs_database

    script:
    """
    set -euo pipefail

    source_db="${mmseqs_database}/${db_name}.mmsdb"
    output_dir="${db_name}_gpu"
    output_db="\${output_dir}/${db_name}.mmsdb"

    for suffix in '' '.dbtype' '.index' '_h' '_h.dbtype' '_h.index'; do
        if [ ! -s "\${source_db}\${suffix}" ]; then
            echo "ERROR: Input MMseqs database is missing \${source_db}\${suffix}." >&2
            exit 1
        fi
    done

    mkdir -p "\${output_dir}" mmseqs_tmp

    mmseqs makepaddedseqdb "\${source_db}" "\${output_db}" --write-lookup 1 --threads ${task.cpus}

    mmseqs createindex "\${output_db}" mmseqs_tmp --index-subset 2 --threads ${task.cpus}

    output_dbtype=\$(od -An -tu4 -N4 "\${output_db}.dbtype" | tr -d '[:space:]')
    if [ -z "\${output_dbtype}" ] || [ \$((output_dbtype & 524288)) -eq 0 ]; then
        echo "ERROR: MMseqs did not create a GPU-padded database at \${output_db}." >&2
        exit 1
    fi

    if [ ! -s "\${output_db}.idx" ] || [ ! -s "\${output_db}.idx.index" ] || [ ! -s "\${output_db}.idx.dbtype" ]; then
        echo "ERROR: MMseqs did not create the subset-2 index for \${output_db}." >&2
        exit 1
    fi

    if grep -Eq '^(3|4|9|10|11|12)[[:space:]]' "\${output_db}.idx.index"; then
        echo "ERROR: The MMseqs index for \${output_db} contains k-mer prefilter data and is not an --index-subset 2 index." >&2
        exit 1
    fi
    """
}
