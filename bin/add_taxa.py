#!/usr/bin/env python
import pandas as pd
import sys

from utils.columns import order_columns

FASTA_COLUMN, combined_annotations_path, ch_taxa_path, output_path = sys.argv[1:5]


# Load combined_annotations.tsv without limiting to specific columns
combined_annotations = pd.read_csv(combined_annotations_path, sep="\t")

# Load ch_taxa TSV with only necessary columns
# Assuming 'user_genome' matches FASTA_COLUMN and 'classification' is the taxonomy information
taxa_columns = ["user_genome", "classification"]
ch_taxa_data = pd.read_csv(ch_taxa_path, sep="\t", usecols=taxa_columns)

# Standardize identifiers in both dataframes, if necessary
combined_annotations[FASTA_COLUMN] = combined_annotations[FASTA_COLUMN]
ch_taxa_data["user_genome"] = ch_taxa_data["user_genome"]

# Check if 'taxonomy' column exists and has at least one non-empty value
if (
    "taxonomy" not in combined_annotations.columns
    or combined_annotations["taxonomy"].isnull().all()
):
    # Proceed with adding taxonomy information by merging based on the corrected columns
    merged_data = pd.merge(
        combined_annotations,
        ch_taxa_data,
        left_on=FASTA_COLUMN,
        right_on="user_genome",
        how="left",
    )

    # Drop the additional 'user_genome' column from ch_taxa in the merged data
    merged_data.drop(columns=["user_genome"], inplace=True)

    # Rename the "classification" column to "taxonomy"
    merged_data.rename(columns={"classification": "taxonomy"}, inplace=True)
else:
    print("Taxonomy information already exists. Skipping addition of taxonomy data.")
    merged_data = combined_annotations

# Save the updated data to raw-annotations.tsv
merged_data = merged_data[order_columns(merged_data.columns)]
merged_data.to_csv(output_path, sep="\t", index=False)

print(f"Updated annotations saved to {output_path}")
