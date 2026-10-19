process RRNA_SCAN {
    label 'process_rrna_scan'
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
    tuple val(sample_names), path('*_processed_rrnas.tsv'), emit: rrna_scan_out, optional: true

    script:
    def batch_inputs = groovy.json.JsonOutput.toJson(
        sample_names.withIndex().collect { name, index -> [name, fastas[index].toString()] }
    )
    """
    #!/usr/bin/env python

    import pandas as pd
    import subprocess
    import io
    from sys import stderr

    FASTA_COLUMN="${params.CONSTANTS.FASTA_COLUMN}"

    def run_barrnap(fasta, input_fasta_name, threads, verbose=True):
        barrnap_command = [
            "barrnap",
            "--threads", str(threads),
            "--kingdom", "bacteria",  # Adjust as necessary
            fasta
        ]
        result = subprocess.run(barrnap_command, capture_output=True, text=True, check=True)
        raw_rrna_str = result.stdout

        if not raw_rrna_str.strip():
            print(f"No rRNAs were detected for {input_fasta_name}.", file=stderr)
            return pd.DataFrame(columns=[FASTA_COLUMN, "query_id", "type", "begin", "end", "e-value", "strand", "note"])  # Ensure this matches RRNA_COLUMNS

        try:
            rrna_df = pd.read_csv(
                io.StringIO(raw_rrna_str),
                sep="\t",
                header=None,
                names=["query_id", "tool_name", "type", "begin", "end", "e-value", "strand", "score", "note"],
                usecols=["query_id", "type", "begin", "end", "e-value", "strand", "note"],
                comment='#'  # This will skip lines starting with '#', including the '##gff-version 3' line
            )
            rrna_df.insert(0, FASTA_COLUMN, input_fasta_name)
            return rrna_df
        except pd.errors.ParserError:
            print(f"Parser error processing barrnap output for {input_fasta_name}. Output may not be in the expected format.", file=stderr)
            return pd.DataFrame(columns=[FASTA_COLUMN, "query_id", "type", "begin", "end", "e-value", "strand", "note"])


    batch_inputs = ${batch_inputs}
    for input_fasta, fasta in batch_inputs:
        rrna_df = run_barrnap(fasta, input_fasta, threads=${task.cpus}, verbose=True)

        if not rrna_df.empty:
            rrna_df.to_csv(f"{input_fasta}_processed_rrnas.tsv", sep="\t", index=False)
        else:
            with open(f"{input_fasta}_processed_rrnas.tsv", "w") as file:
                file.write("NULL")

    """
}
