#!/usr/bin/env python
from os import path
from datetime import datetime
from shutil import move, rmtree
from glob import glob
import logging
import subprocess
import gzip
import argparse
from pathlib import Path
import re
import sqlite3
from itertools import islice
from tempfile import TemporaryDirectory
from contextlib import closing


LOGGER = logging.getLogger("database_processing.log")


def prepare_databases(
    kegg_loc,
    kegg_kff_loc,
    output_dir="kegg",
    kegg_download_date=None,
    threads=10,
):
    # setup temp, logging, and db_handler
    output_dir = Path(output_dir)
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    temporary = output_dir / "database_files"
    temporary.mkdir()

    LOGGER.info("Database preparation started")
    LOGGER.info("Processing KEGG database")

    processed_locs = process_kegg(
        kegg_loc=kegg_loc,
        output_dir=output_dir,
        kegg_kff_loc=kegg_kff_loc,
        threads=threads,
        download_date=kegg_download_date,
    )
    # Process databases

    for k, v in processed_locs.items():
        final_dest = output_dir / path.basename(v)
        if v != final_dest:
            for db_file in glob("%s*" % v):
                move(db_file, path.join(output_dir, path.basename(db_file)))
            v = path.join(output_dir, path.basename(v))
        # update_dram_forms the settings per OUTPUT fill, including the process_settings
        #  and database_settings, which are per input file.
        LOGGER.info(f"Moved {k} to final destination")


def process_kegg(
    kegg_loc,
    output_dir,
    kegg_kff_loc,
    download_date=None,
    threads=10,
):
    threads = threads or 10  # make sure cli option is >=1 and not None
    if not download_date:
        download_date = get_iso_date()
    kegg_mod_loc = path.join(output_dir, "kegg.mod.fa")
    with open(kegg_mod_loc, "w") as output:
        output.writelines(
            generate_modified_kegg_fasta(kegg_loc, kegg_kff_loc, output_dir)
        )
    # make mmseqsdb from modified kegg fasta
    kegg_mmseqs_db = path.join(output_dir, "kegg.mmsdb")
    create_mmseqs(
        kegg_mod_loc,
        kegg_mmseqs_db,
        # create_index=True,
        threads=threads,
    )
    LOGGER.info("KEGG database processed")
    return {"kegg": kegg_mmseqs_db}


def create_mmseqs(fasta_loc, output_loc, threads):
    """Takes a fasta file and makes a mmseqs2 database for use in blast searching and hmm searching with mmseqs2."""
    LOGGER.info(f"Creating MMseqs2 database for {fasta_loc}...")
    subprocess.run(
        ["mmseqs", "createdb", fasta_loc, output_loc],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tmp_dir = path.join(path.dirname(output_loc), "tmp")
    LOGGER.info(f"Created MMseqs2 database for {fasta_loc}... Now creating index")
    subprocess.run(
        ["mmseqs", "createindex", output_loc, tmp_dir, "--threads", str(threads)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    LOGGER.info(f"MMseqs2 database created at {output_loc}")

    # Remove the temporary directory
    if path.exists(tmp_dir):
        rmtree(tmp_dir)
        print(f"Removed temporary directory: {tmp_dir}")


def open_text(filename):
    """Detect gzip by content, since Nextflow may rename staged input files."""
    with open(filename, "rb") as source:
        compressed = source.read(2) == b"\x1f\x8b"
    return gzip.open(filename, "rt") if compressed else open(filename)


def kff_annotations(kegg_kff):
    """Read KEGG's 11-column tab-delimited KFF, preserving empty fields.

    Column 1 is the gene ID, 10 is the KO assignment, and 11 is the
    KO description (including EC annotations). KFF has no protein sequence.
    """
    with open_text(kegg_kff) as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) != 11 or not fields[0].strip():
                raise ValueError(
                    f"{kegg_kff}:{line_number}: expected 11 tab-separated KFF fields and a gene ID"
                )
            kos = re.findall(r"\bK\d{5}\b", fields[9])
            annotation = "; ".join(dict.fromkeys(kos + [fields[10].strip()])).strip(
                "; "
            )
            if annotation:
                yield fields[0].strip(), annotation


def generate_modified_kegg_fasta(kegg_fasta, kegg_kff, temporary_dir=None):
    """Stream FASTA with KFF metadata joined by full gene ID using a disk index.

    Sequences and identifiers are preserved, including genes absent from KFF.
    Repeated identical KFF annotations are ignored; distinct annotations for the
    same gene are retained. Memory use does not grow with the number of genes.
    """
    with TemporaryDirectory(prefix="kegg_metadata_", dir=temporary_dir) as directory:
        with closing(
            sqlite3.connect(path.join(directory, "annotations.sqlite"))
        ) as connection:
            connection.execute(
                "CREATE TABLE annotations (gene TEXT, annotation TEXT, "
                "PRIMARY KEY (gene, annotation)) WITHOUT ROWID"
            )
            annotations = iter(kff_annotations(kegg_kff))
            while batch := list(islice(annotations, 10000)):
                connection.executemany(
                    "INSERT OR IGNORE INTO annotations VALUES (?, ?)", batch
                )
                connection.commit()

            missing = 0
            with open_text(kegg_fasta) as source:
                for line in source:
                    if not line.startswith(">"):
                        yield line
                        continue
                    header = line[1:].rstrip("\r\n")
                    fields = header.split(maxsplit=1)
                    if not fields:
                        raise ValueError(f"{kegg_fasta}: empty FASTA identifier")
                    gene = fields[0]
                    description = fields[1] if len(fields) > 1 else ""
                    rows = connection.execute(
                        "SELECT annotation FROM annotations WHERE gene = ? ORDER BY annotation",
                        (gene,),
                    ).fetchall()
                    if not rows:
                        missing += 1
                    for (annotation,) in rows:
                        for part in annotation.split("; "):
                            if part and part not in description:
                                description += ("; " if description else "") + part
                    yield ">" + gene + (" " + description if description else "") + "\n"
            if missing:
                LOGGER.warning(
                    "%s FASTA records had no KFF annotation; original headers retained",
                    missing,
                )


def get_iso_date():
    return datetime.today().strftime("%Y%m%d")


def main():
    parser = argparse.ArgumentParser(description="Prepare KEGG database")
    parser.add_argument(
        "--kegg_loc",
        required=True,
        type=str,
        help="Path to the KEGG peptide FASTA (.pep or .pep.gz)",
    )
    parser.add_argument(
        "--kegg_kff_loc",
        required=True,
        type=str,
        help="Path to matching KEGG annotations (.kff or .kff.gz)",
    )
    parser.add_argument(
        "--output_dir", type=str, help="Path to the output directory", default="kegg"
    )
    parser.add_argument(
        "--download_date",
        type=str,
        help="Date of the KEGG download, if not included, will use today's date",
    )
    parser.add_argument(
        "--threads", type=int, help="Number of threads to use", default=10
    )
    args = parser.parse_args()

    prepare_databases(
        kegg_loc=args.kegg_loc,
        kegg_kff_loc=args.kegg_kff_loc,
        output_dir=args.output_dir,
        kegg_download_date=args.download_date,
        threads=args.threads,
    )


if __name__ == "__main__":
    main()
