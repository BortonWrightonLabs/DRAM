process ADD_TAXA {
    label 'process_small'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_biopython:81f6b2a8fb71cdc6' :
        'community.wave.seqera.io/library/python_pandas_biopython:7df21d027f67112e' }"

    input:
    file( combined_annotations )
    file( ch_taxa )

    output:
    path("raw-annotations.tsv"), emit: annots_taxa_out, optional: true

    script:
    """
    #!/usr/bin/env python

    import pandas as pd

    FASTA_COLUMN="${params.CONSTANTS.FASTA_COLUMN}"

    # Corrected file paths
    combined_annotations_path = "${combined_annotations}"
    ch_taxa_path = "${ch_taxa}"

    # Load combined_annotations.tsv without limiting to specific columns
    combined_annotations = pd.read_csv(combined_annotations_path, sep='\t')

    # Load ch_taxa TSV with only necessary columns
    # Assuming 'user_genome' matches FASTA_COLUMN and 'classification' is the taxonomy information
    taxa_columns = ['user_genome', 'classification']
    ch_taxa_data = pd.read_csv(ch_taxa_path, sep='\t', usecols=taxa_columns)

    # Standardize identifiers in both dataframes, if necessary
    combined_annotations[FASTA_COLUMN] = combined_annotations[FASTA_COLUMN]
    ch_taxa_data['user_genome'] = ch_taxa_data['user_genome']

    # Check if 'taxonomy' column exists and has at least one non-empty value
    if 'taxonomy' not in combined_annotations.columns or combined_annotations['taxonomy'].isnull().all():
        # Proceed with adding taxonomy information by merging based on the corrected columns
        merged_data = pd.merge(combined_annotations, ch_taxa_data, left_on=FASTA_COLUMN, right_on="user_genome", how="left")

        # Drop the additional 'user_genome' column from ch_taxa in the merged data
        merged_data.drop(columns=['user_genome'], inplace=True)

        # Rename the "classification" column to "taxonomy"
        merged_data.rename(columns={"classification": "taxonomy"}, inplace=True)
    else:
        print("Taxonomy information already exists. Skipping addition of taxonomy data.")
        merged_data = combined_annotations

    # Save the updated data to raw-annotations.tsv
    output_path = "raw-annotations.tsv"  # Changed to avoid overwriting the original file
    merged_data.to_csv(output_path, sep='\t', index=False)

    print(f"Updated annotations saved to {output_path}")


    """
}
