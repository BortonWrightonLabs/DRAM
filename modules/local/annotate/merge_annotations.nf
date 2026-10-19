process MERGE_ANNOTATIONS {
    label 'process_small'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:1742d882bc99fed5' :
        'community.wave.seqera.io/library/python_pandas_polars_hmmer_pruned:6d5bc9dfeca29b70' }"

    input:
    path( ch_annotations, stageAs: "annotations/*" )

    output:
    path "raw-merged-annotations.tsv", emit: ch_merged_annots_out

    script:
    """
    #!/usr/bin/env python

    import pandas as pd
    import os
    import glob

    FASTA_COLUMN="${params.CONSTANTS.FASTA_COLUMN}"

    def assign_rank(row):
        rank = 'E'
        if row.get('kegg_bitScore', 0) > 350:
            rank = 'A'
        elif row.get('uniref_bitScore', 0) > 350:
            rank = 'B'
        elif row.get('kegg_bitScore', 0) > 60 or row.get('uniref_bitScore', 0) > 60:
            rank = 'C'
        elif any(row.get(f"{db}_bitScore", 0) > 60 for db in ['pfam', 'dbcan', 'merops']):
            rank = 'D'
        return rank

    def convert_bit_scores_to_numeric(df):
        for col in df.columns:
            if "_bitScore" in col:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    annotations_dir = "annotations"
    dfs = []

    for file_path in glob.glob(os.path.join(annotations_dir, '*.tsv')):
        current_df = pd.read_csv(file_path, sep='\t')
        current_df = convert_bit_scores_to_numeric(current_df)
        dfs.append(current_df)

    merged_df = pd.concat(dfs, ignore_index=True)

    # Removing duplicates
    merged_df.drop_duplicates(inplace=True)

    merged_df['rank'] = merged_df.apply(assign_rank, axis=1)

    # Sorting by 'query_id'
    merged_df.sort_values(by='query_id', inplace=True)

    base_columns = ['query_id', FASTA_COLUMN, 'start_position', 'stop_position', 'strandedness', 'rank']
    kegg_columns = [col for col in merged_df.columns if col.startswith('kegg_')]
    essential_columns = ['Completeness', 'Contamination', 'taxonomy']
    other_columns = [col for col in merged_df.columns if col not in base_columns + kegg_columns + essential_columns]
    final_columns = base_columns + kegg_columns + other_columns + [col for col in essential_columns if col in merged_df.columns]

    merged_df = merged_df[final_columns]

    merged_file_path = "raw-merged-annotations.tsv"
    merged_df.to_csv(merged_file_path, sep='\t', index=False)

    print(f"Merged annotations saved to {merged_file_path}")
    """
}
