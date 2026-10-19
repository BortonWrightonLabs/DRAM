process ADD_ANNOTATIONS {
    label 'process_small'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_biopython:81f6b2a8fb71cdc6' :
        'community.wave.seqera.io/library/python_pandas_biopython:7df21d027f67112e' }"

    input:
    path( old_annotations, stageAs: "old_annotations.tsv" )
    path( new_annotations, stageAs: "new_annotations.tsv" )


    output:
    path "raw-combined-annotations.tsv", emit: combined_annots_out

    script:
    """
    #!/usr/bin/env python
    import pandas as pd

    FASTA_COLUMN="${params.CONSTANTS.FASTA_COLUMN}"

    # Load the annotations into DataFrames
    df_old = pd.read_csv("old_annotations.tsv", sep='\t')
    df_new = pd.read_csv("new_annotations.tsv", sep='\t')

    # Define key columns for merging
    key_columns = ['query_id', FASTA_COLUMN, 'start_position', 'stop_position', 'strandedness']

    # Perform an outer merge on the key columns
    merged_df = pd.merge(df_old, df_new, on=key_columns, how='outer', suffixes=('_old', '_new'))

    # Handle duplicate non-key columns
    non_key_columns_old = [col for col in df_old.columns if col not in key_columns]
    non_key_columns_new = [col for col in df_new.columns if col not in key_columns]
    duplicate_columns = set(non_key_columns_old) & set(non_key_columns_new) - set(key_columns)

    for col in duplicate_columns:
        # Create a new column that concatenates information from the old and new columns, if both are non-null
        merged_df[col] = merged_df.apply(lambda x: str(x[col + '_old']) + "; " + str(x[col + '_new'])
                                        if pd.notnull(x[col + '_old']) and pd.notnull(x[col + '_new'])
                                        else x[col + '_old'] if pd.notnull(x[col + '_old'])
                                        else x[col + '_new'], axis=1)
        # Drop the old and new columns after merging their data
        merged_df.drop(columns=[col + '_old', col + '_new'], inplace=True)

    # For columns not in duplicate_columns but existing with suffixes, remove the suffix and keep the value
    for col in merged_df.columns:
        if '_old' in col or '_new' in col:
            clean_col_name = col.replace('_old', '').replace('_new', '')
            if clean_col_name not in merged_df.columns: # If the clean name doesn't already exist
                merged_df.rename(columns={col: clean_col_name}, inplace=True)
            else:
                merged_df.drop(columns=[col], inplace=True) # If it exists, likely handled above, drop the column

    # Save the merged DataFrame
    merged_df.to_csv("raw-combined-annotations.tsv", sep='\t', index=False)
    print("Merged annotations saved to merged_annotations.tsv")

    """
}
