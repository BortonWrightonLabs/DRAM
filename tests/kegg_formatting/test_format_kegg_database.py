"""Run with python -m unittest discover -s tests/kegg_formatting -v."""

import gzip
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import os
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "format_kegg", ROOT / "bin/format_kegg_database.py"
)
formatter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formatter)


def kff_row(gene, ko="", description=""):
    return (
        "\t".join(
            [gene, "CDS", "3", "12", "1..12", "", "", "", "original", ko, description]
        )
        + "\n"
    )


class KeggFormattingTests(unittest.TestCase):
    def test_join_preserves_sequences_and_missing_genes(self):
        with tempfile.TemporaryDirectory() as directory:
            pep = Path(directory) / "input.pep"
            kff = Path(directory) / "input.kff"
            pep.write_text(
                ">chyl:CE91St63_15060 bile-acid 7-alpha-dehydratase\nMA\nAA\n"
                ">org:bare\nMBB\n>org:missing original\nMCC\n>org:empty original\nMDD\n"
            )
            annotation = kff_row(
                "chyl:CE91St63_15060",
                "K15872",
                "baiE; bile-acid 7alpha-dehydratase [EC:4.2.1.106]",
            )
            kff.write_text(
                annotation
                + annotation
                + kff_row("org:bare", "K00001 K00002", "enzyme [EC:1.2.3.- 1.2.3.4]")
                + kff_row("org:empty")
            )
            result = "".join(
                formatter.generate_modified_kegg_fasta(pep, kff, directory)
            )
            self.assertEqual(
                result,
                ">chyl:CE91St63_15060 bile-acid 7-alpha-dehydratase; K15872; baiE; bile-acid 7alpha-dehydratase [EC:4.2.1.106]\nMA\nAA\n"
                ">org:bare K00001; K00002; enzyme [EC:1.2.3.- 1.2.3.4]\nMBB\n"
                ">org:missing original\nMCC\n>org:empty original\nMDD\n",
            )
            self.assertEqual(list(Path(directory).glob("kegg_metadata_*")), [])

    def test_gzip_and_existing_annotation(self):
        with tempfile.TemporaryDirectory() as directory:
            pep = Path(directory) / "input.pep.gz"
            kff = Path(directory) / "input.kff.gz"
            with gzip.open(pep, "wt") as output:
                output.write(">org:gene enzyme [EC:1.2.3.4]; K00001\nMABC\n")
            with gzip.open(kff, "wt") as output:
                output.write(kff_row("org:gene", "ko:K00001", "enzyme [EC:1.2.3.4]"))
            result = "".join(formatter.generate_modified_kegg_fasta(pep, kff))
            self.assertEqual(result, ">org:gene enzyme [EC:1.2.3.4]; K00001\nMABC\n")

    def test_malformed_kff_fails_with_location(self):
        with tempfile.TemporaryDirectory() as directory:
            kff = Path(directory) / "bad.kff"
            kff.write_text("org:gene CDS 3\n")
            with self.assertRaisesRegex(
                ValueError, r"bad.kff:1: expected 11 tab-separated"
            ):
                list(formatter.kff_annotations(kff))

    def test_build_uses_enriched_fasta(self):
        with tempfile.TemporaryDirectory() as directory:
            pep = Path(directory) / "input.pep"
            kff = Path(directory) / "input.kff"
            output = Path(directory) / "output"
            pep.write_text(">org:gene original\nMAAA\n")
            kff.write_text(kff_row("org:gene", "K15872", "enzyme [EC:4.2.1.106]"))
            with patch.object(formatter, "create_mmseqs") as create:
                formatter.prepare_databases(pep, kff, output, threads=2)
            create.assert_called_once_with(
                str(output / "kegg.mod.fa"), str(output / "kegg.mmsdb"), threads=2
            )
            self.assertIn("[EC:4.2.1.106]", (output / "kegg.mod.fa").read_text())

    @unittest.skipUnless(shutil.which("nextflow"), "Nextflow is not installed")
    def test_nextflow_modules_with_directory_and_explicit_files(self):
        # Run real Nextflow modules and the real formatter; mock only expensive
        # MMseqs database construction so this test needs no KEGG installation.
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            organism = project / "organisms with spaces" / "org"
            organism.mkdir(parents=True)
            pep = organism / "org.pep"
            kff = organism / "org.kff"
            pep.write_text(">org:gene original\nMAAA\n")
            kff.write_text(kff_row("org:gene", "K15872", "enzyme [EC:4.2.1.106]"))
            pep_gz = project / "input.pep.gz"
            kff_gz = project / "input.kff.gz"
            with gzip.open(pep_gz, "wt") as output:
                output.write(pep.read_text())
            with gzip.open(kff_gz, "wt") as output:
                output.write(kff.read_text())
            binaries = project / "bin"
            binaries.mkdir()
            shutil.copy2(ROOT / "bin/format_kegg_database.py", binaries)
            mmseqs = binaries / "mmseqs"
            mmseqs.write_text(
                "#!/usr/bin/env python\nimport sys\nfrom pathlib import Path\n"
                "if sys.argv[1] == 'createdb':\n"
                "    Path(sys.argv[3]).write_text('mock database')\n"
                "elif sys.argv[1] == 'createindex':\n"
                "    Path(sys.argv[3]).mkdir()\n"
            )
            mmseqs.chmod(0o755)
            (project / "main.nf").write_text(f"""
include {{ CAT_KEGG_PEP }} from '{ROOT}/modules/local/database/cat_kegg_pep.nf'
include {{ FORMAT_KEGG_DB }} from '{ROOT}/modules/local/database/format_kegg_db.nf'
include {{ FORMAT_KEGG_DB as FORMAT_DIRECT }} from '{ROOT}/modules/local/database/format_kegg_db.nf'
params.threads = 1
workflow {{
    CAT_KEGG_PEP(file('{organism.parent}'))
    FORMAT_KEGG_DB(CAT_KEGG_PEP.out.kegg_pep, CAT_KEGG_PEP.out.kegg_kff, '')
    FORMAT_DIRECT(file('{pep_gz}'), file('{kff_gz}'), '20260528')
}}
""")
            environment = dict(
                os.environ,
                NXF_HOME=os.environ.get("NXF_HOME", str(Path.home() / ".nextflow")),
            )
            result = subprocess.run(
                ["nextflow", "run", "main.nf", "-ansi-log", "false", "--threads", "1"],
                cwd=project,
                env=environment,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            fastas = list(project.glob("work/*/*/kegg/kegg.mod.fa"))
            self.assertEqual(len(fastas), 2, result.stdout + result.stderr)
            for fasta in fastas:
                self.assertEqual(
                    fasta.read_text(),
                    ">org:gene original; K15872; enzyme [EC:4.2.1.106]\nMAAA\n",
                )


if __name__ == "__main__":
    unittest.main()
