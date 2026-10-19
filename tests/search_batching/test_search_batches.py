"""Run with NXF_VER=25.04.7 (or 25.10.0) python3 -m unittest discover -s tests/search_batching -v.

Runs actual Nextflow workflows and generated search scripts with mock executables.
Sparse input files exercise large classes without allocating their logical size.
"""

import csv
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


class SearchBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dram-search-batches-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.fixtures = self.folder / "fixtures"
        self.fixtures.mkdir()
        for name in ["alpha", "beta", "nohit", "medium", "large"]:
            for suffix in [".faa", ".mmsdb", ".mmsdb.index", ".tsv"]:
                path = self.fixtures / (name + suffix)
                path.write_text(name + "\n")
                if suffix in [".faa", ".mmsdb"] and name in ["medium", "large"]:
                    with path.open("r+b") as handle:
                        handle.truncate(
                            (500 * 1024**2 if name == "medium" else 2 * 1024**3)
                        )
        (self.fixtures / "info.tsv").write_text("info\n")
        (self.fixtures / "target.hmm").write_text("hmm\n")
        with (self.fixtures / "target.hmm").open("r+b") as handle:
            handle.truncate(21 * 1024**3)
        target = self.fixtures / "target"
        target.mkdir()
        for db in ["kegg", "camper"]:
            (target / (db + ".mmsdb")).write_text(db + "\n")
        with (target / "database-size-is-ignored").open("wb") as handle:
            handle.truncate(21 * 1024**3)
        mock_bin = self.fixtures / "bin"
        mock_bin.mkdir()
        for name in [
            "hmm_search.py",
            "hmm_parser.py",
            "mmseqs",
            "mmseqs_add_descriptions.py",
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
    search_batch_size = 1
    search_batch_max_size = '200.MB'
    duplicate_test = false
}}
includeConfig '{ROOT}/conf/base.config'
process {{
    executor = 'local'
    queue = 'ordinary'
    beforeScript = {{ "export PATH={mock_bin}:\\$PATH\\nprintf '%s\\\\n' '${{task.cpus}}|${{task.memory}}|${{task.time}}|${{task.queue}}' > test_resources.txt" }}
    withName: '.*:MMSEQS_KEGG:SEARCH_.*' {{ queue = 'kegg_only' }}
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
        result = subprocess.run(
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
        return result

    def trace(self):
        with (self.folder / "trace.tsv").open() as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    def test_helpers(self):
        result = self.run_nextflow("helpers.nf")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Search batch helper assertions passed", result.stdout)

    def test_single_inputs_and_array_one(self):
        result = self.run_nextflow(
            "main.nf", "--search_batch_size", "1", "--job_array_size", "1"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.trace()), 20)

    def test_duplicate_names_fail(self):
        result = self.run_nextflow("helpers.nf", "--duplicate_test", "true")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("sample names must be unique", result.stdout)

    def test_batches_outputs_caps_selectors_and_resume(self):
        args = ["--search_batch_size", "2"]
        result = self.run_nextflow("main.nf", *args)
        self.assertEqual(result.returncode, 0, result.stdout)
        rows = self.trace()
        self.assertEqual(len(rows), 17)
        for row in rows:
            resource = (Path(row["workdir"]) / "test_resources.txt").read_text().strip()
            is_index = "INDEX_QUERIES" in row["name"]
            expected_queue = (
                "kegg_only" if "MMSEQS_KEGG:" in row["name"] else "ordinary"
            )
            expected_time = (
                "1h"
                if is_index
                else (
                    "16h"
                    if "SEARCH_SMALL" in row["name"]
                    else ("1d 8h" if "SEARCH_MEDIUM" in row["name"] else "7d")
                )
            )
            self.assertEqual(resource, f"1|1 GB|{expected_time}|{expected_queue}")
        result = self.run_nextflow("main.nf", *args, "-resume")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(all(row["status"] == "CACHED" for row in self.trace()))

    def test_query_byte_limit_and_lower_time_cap(self):
        result = self.run_nextflow(
            "main.nf",
            "--search_batch_size",
            "10",
            "--search_batch_max_size",
            "1.B",
            "--max_time",
            "2.h",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.trace()), 20)
        for row in self.trace():
            expected_time = "1h" if "INDEX_QUERIES" in row["name"] else "2h"
            self.assertIn(
                f"|{expected_time}|",
                (Path(row["workdir"]) / "test_resources.txt").read_text(),
            )

    def test_member_failure_fails_batch(self):
        result = self.run_nextflow(
            "main.nf", "--search_batch_size", "2", fail_sample="beta"
        )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("42", result.stdout)

    def test_batches_inside_slurm_arrays(self):
        with self.config.open("a") as handle:
            handle.write(
                "\nprocess.executor = 'slurm'\nexecutor.pollInterval = '100 ms'\nexecutor.queueStatInterval = '100 ms'\n"
            )
        result = self.run_nextflow(
            "main.nf", "--search_batch_size", "2", "--job_array_size", "2"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.trace()), 17)
        submissions = (self.folder / "slurm-submissions.tsv").read_text().splitlines()
        self.assertTrue(
            any(line.startswith("array\t") for line in submissions), submissions
        )
        self.assertLess(len(submissions), 17)


if __name__ == "__main__":
    unittest.main()
