process TRNA_SCAN {
    label 'process_trna_scan'
    label 'process_array'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] ?
        'oras://community.wave.seqera.io/library/python_pandas_barrnap_trnascan-se:e21b0760a084ff3c' :
        'community.wave.seqera.io/library/python_pandas_barrnap_trnascan-se:ed2ab26abf39304b' }"

    tag { sample_names.join(',') }

    input:
    tuple val(resource_class), val(sample_names),
        path(fastas, stageAs: 'inputs/input??.fa', arity: '1..*')

    output:
    tuple val(sample_names), path('*_processed_trnas.tsv'), emit: trna_scan_out, optional: true

    script:
    def batch_inputs = groovy.json.JsonOutput.toJson(
        sample_names.withIndex().collect { name, index -> [name, fastas[index].toString()] }
    )
    """
    #!/usr/bin/env python

    import pandas as pd
    import subprocess
    import os

    # Set TMPDIR to ./tmp
    os.environ['TMPDIR'] = './tmp'

    FASTA_COLUMN="${params.CONSTANTS.FASTA_COLUMN}"

    # Create the temporary directory if it doesn't exist
    os.makedirs(os.environ['TMPDIR'], exist_ok=True)

    def process_trnascan_output(input_file, output_file, input_fasta_name):
        try:
            # Read the input file into a DataFrame
            trna_frame = pd.read_csv(input_file, sep="\t", skiprows=[0, 2], engine='python')

            # Proceed with processing if trna_frame is not empty
            if not trna_frame.empty:
                # Strip leading and trailing spaces from column names
                trna_frame.columns = trna_frame.columns.str.strip()

                # Add a new FASTA_COLUMN column and populate it with the input_fasta_name value
                trna_frame.insert(0, FASTA_COLUMN, input_fasta_name)

                ## Check if "Note" column is present
                #if "Note" in trna_frame.columns:
                #    # Process the "Note" column to update the "Type" column
                #    trna_frame["Type"] = trna_frame.apply(lambda row: row["Type"] + " (pseudo)" if str(row["Note"]).lower().startswith("pseudo") else row["Type"], axis=1)

                #    # Drop the processed "Note" column
                #    trna_frame = trna_frame.drop(columns=["Note"])

                # Keep only the first occurrence of "Begin" and "End" columns
                trna_frame = trna_frame.loc[:, ~trna_frame.columns.duplicated(keep='first')]

                # Remove columns starting with "Begin" or "End"
                trna_frame = trna_frame.loc[:, ~trna_frame.columns.str.match('(Begin|End)\\.')]

                # Rename specified columns
                trna_frame = trna_frame.rename(columns={"Name": "query_id", "Begin": "begin", "End": "end", "Type": "type", "Codon": "codon", "Score": "score", "Note": "note"})

                # Create the "gene_id" column by concatenating "type" and "codon"
                trna_frame["gene_id"] = trna_frame["type"] + " (" + trna_frame["codon"] + ")"

                # Check if DataFrame after processing is still not empty
                if not trna_frame.empty:
                    # Write the processed DataFrame to the output file
                    trna_frame.to_csv(output_file, sep="\t", index=False)
        except pd.errors.EmptyDataError:
            # The input file is empty or only contains headers, write "NULL" to output
            pass

    batch_inputs = ${batch_inputs}
    for input_fasta, fasta in batch_inputs:
        # Run tRNAscan-SE with the necessary input to avoid prompts
        trna_out = f"{input_fasta}_trna_out.txt"
        subprocess.run(["tRNAscan-SE", "-G", "-o", trna_out, "--thread", "${task.cpus}", fasta], input=b'O\\n', check=True)

        # Process tRNAscan-SE output
        process_trnascan_output(trna_out, f"{input_fasta}_processed_trnas.tsv", input_fasta)
    """
}
