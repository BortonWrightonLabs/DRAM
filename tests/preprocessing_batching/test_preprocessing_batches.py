"""Integration checks for CALL_GENES, tRNAscan-SE, and Barrnap input batching."""

import csv
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


class PreprocessingBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dram-preprocessing-batches-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.fixtures = self.folder / "fixtures"
        self.fixtures.mkdir()
        for name in ["alpha", "beta", "gamma", "medium", "large"]:
            path = self.fixtures / (name + ".fa")
            path.write_text(name + "\n")
            if name in ["medium", "large"]:
                with path.open("r+b") as handle:
                    handle.truncate(
                        (500 * 1024**2 if name == "medium" else 2 * 1024**3)
                    )

        mock_bin = self.fixtures / "bin"
        mock_bin.mkdir()
        for name in [
            "python",
            "reformat.sh",
            "prodigal",
            "parse_faa.sh",
            "quast.py",
            "process_quast.py",
            "gff_replace_id_with_scaffold_gene_number.sh",
            "tRNAscan-SE",
            "barrnap",
            "sbatch",
            "squeue",
            "scancel",
        ]:
            script = mock_bin / name
            shutil.copyfile(HERE / "mock_tool.py", script)
            script.chmod(0o755)

        self.config = self.folder / "test.config"
        self.config.write_text(f"""
params {{
    max_cpus = 1
    max_memory = '1.GB'
    max_time = '168.h'
    resource_class_small_max_size = '200.MB'
    resource_class_medium_max_size = '1.GB'
    job_array_size = 0
    call_batch_size = 1
    call_batch_max_size = '200.MB'
    rna_batch_size = 1
    rna_batch_max_size = '200.MB'
    min_contig_len = 1
    prodigal_mode = 'meta'
    prodigal_trans_table = 11
    duplicate_test = false
    CONSTANTS = [FASTA_COLUMN: 'fasta']
}}
includeConfig '{ROOT}/conf/base.config'
process {{
    executor = 'local'
    beforeScript = {{ "export PATH={mock_bin}:\\$PATH\\nprintf '%s\\n' '${{task.cpus}}|${{task.memory}}|${{task.time}}' > test_resources.txt" }}
}}
trace {{
    enabled = true
    file = '{self.folder}/trace.tsv'
    fields = 'task_id,name,status,workdir'
    overwrite = true
}}
""")

    def run_nextflow(self, script, *args, fail_sample=None):
        env = dict(os.environ, NXF_OFFLINE="true", NXF_ANSI_LOG="false")
        env["PATH"] = str(self.fixtures / "bin") + os.pathsep + env["PATH"]
        env["MOCK_SLURM_LOG"] = str(self.folder / "slurm-submissions.tsv")
        if fail_sample:
            env["FAIL_SAMPLE"] = fail_sample
        return subprocess.run(
            [
                "nextflow",
                "-C",
                str(self.config),
                "run",
                str(HERE / script),
                "-work-dir",
                str(self.folder / "work"),
                "--fixtures",
                str(self.fixtures),
                *args,
            ],
            cwd=self.folder,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
        )

    def trace(self):
        with (self.folder / "trace.tsv").open() as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    def test_helpers(self):
        result = self.run_nextflow("helpers.nf")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Preprocessing batch helper assertions passed", result.stdout)

    def test_duplicate_names_fail(self):
        result = self.run_nextflow("helpers.nf", "--duplicate_test", "true")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("sample names must be unique", result.stdout)

    def test_defaults_disable_batching(self):
        result = self.run_nextflow("main.nf")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.trace()), 15)

    def test_call_workflow_preserves_derived_size_metadata(self):
        result = self.run_nextflow("call_workflow.nf", "--call_batch_size", "2")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.trace()), 5)

    def test_batches_outputs_resources_and_resume(self):
        args = ["--call_batch_size", "2", "--rna_batch_size", "2"]
        result = self.run_nextflow("main.nf", *args)
        self.assertEqual(result.returncode, 0, result.stdout)
        rows = self.trace()
        self.assertEqual(len(rows), 12)
        for row in rows:
            resource = (Path(row["workdir"]) / "test_resources.txt").read_text().strip()
            expected_time = (
                "8h"
                if "_SMALL" in row["name"]
                else ("16h" if "_MEDIUM" in row["name"] else "7d")
            )
            self.assertEqual(resource, f"1|1 GB|{expected_time}")
        result = self.run_nextflow("main.nf", *args, "-resume")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(all(row["status"] == "CACHED" for row in self.trace()))

    def test_per_input_byte_limit(self):
        result = self.run_nextflow(
            "main.nf",
            "--call_batch_size",
            "10",
            "--rna_batch_size",
            "10",
            "--call_batch_max_size",
            "1.B",
            "--rna_batch_max_size",
            "1.B",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.trace()), 15)

    def test_member_failure_fails_each_process_family(self):
        result = self.run_nextflow(
            "main.nf",
            "--call_batch_size",
            "2",
            "--rna_batch_size",
            "2",
            fail_sample="beta",
        )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("42", result.stdout)

    def test_batches_inside_slurm_arrays(self):
        with self.config.open("a") as handle:
            handle.write(
                "\nprocess.executor = 'slurm'\nexecutor.pollInterval = '100 ms'\nexecutor.queueStatInterval = '100 ms'\n"
            )
        result = self.run_nextflow(
            "main.nf",
            "--call_batch_size",
            "2",
            "--rna_batch_size",
            "2",
            "--job_array_size",
            "2",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.trace()), 12)
        submissions = (self.folder / "slurm-submissions.tsv").read_text().splitlines()
        self.assertTrue(
            any(line.startswith("array\t") for line in submissions), submissions
        )
        self.assertLess(len(submissions), 12)


if __name__ == "__main__":
    unittest.main()
