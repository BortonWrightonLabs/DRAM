#!/usr/bin/env python
import pandas as pd
import os
import sys

from utils.columns import order_columns
import glob

FASTA_COLUMN, annotations_dir, merged_file_path = sys.argv[1:4]


def assign_rank(row):
    rank = "E"
    if row.get("kegg_bitScore", 0) > 350:
        rank = "A"
    elif row.get("uniref_bitScore", 0) > 350:
        rank = "B"
    elif row.get("kegg_bitScore", 0) > 60 or row.get("uniref_bitScore", 0) > 60:
        rank = "C"
    elif any(row.get(f"{db}_bitScore", 0) > 60 for db in ["pfam", "dbcan", "merops"]):
        rank = "D"
    return rank


def convert_bit_scores_to_numeric(df):
    for col in df.columns:
        if "_bitScore" in col:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


dfs = []

for file_path in glob.glob(os.path.join(annotations_dir, "*.tsv")):
    current_df = pd.read_csv(file_path, sep="\t")
    current_df = convert_bit_scores_to_numeric(current_df)
    dfs.append(current_df)

merged_df = pd.concat(dfs, ignore_index=True)

# Removing duplicates
merged_df.drop_duplicates(inplace=True)

merged_df["rank"] = merged_df.apply(assign_rank, axis=1)

# Sorting by 'query_id'
merged_df.sort_values(by="query_id", inplace=True)

merged_df = merged_df[order_columns(merged_df.columns)]

merged_df.to_csv(merged_file_path, sep="\t", index=False)

print(f"Merged annotations saved to {merged_file_path}")
