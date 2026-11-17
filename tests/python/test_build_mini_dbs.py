import gzip
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "build_mini_dbs", ROOT / "tests/scripts/build_mini_dbs.py"
)
build_mini_dbs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_mini_dbs)


def hmm_record(name, length):
    return (
        "HMMER3/f [3.4 | Aug 2023]\n"
        f"NAME  {name}\n"
        f"LENG  {length}\n"
        "HMM          A        C\n"
        "  1   2.1 2.2\n"
        "//\n"
    )


class SubsetHmmTests(unittest.TestCase):
    def test_keeps_only_named_records_in_source_order(self):
        # Hit lists such as fegenie_ids follow database order, so order must not change.
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "all.hmm"
            source.write_text(
                hmm_record("K3", 30) + hmm_record("K2", 20) + hmm_record("K1", 10)
            )

            subset = build_mini_dbs.subset_hmm(source, {"K3", "K1"})

        self.assertEqual(subset, hmm_record("K3", 30) + hmm_record("K1", 10))

    def test_missing_name_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "all.hmm"
            source.write_text(hmm_record("K1", 10))

            with self.assertRaisesRegex(ValueError, "K9"):
                build_mini_dbs.subset_hmm(source, {"K1", "K9"})


KO_LIST = (
    "knum\tthreshold\tscore_type\tdefinition\n"
    "K1\t10.0\tfull\tone\n"
    "K2\t20.0\tdomain\ttwo\n"
    "K3\t30.0\tfull\tthree [EC:1.1.1.1]\n"
)


class KofamBuildTests(unittest.TestCase):
    def run_kofam(self, root, profiles, ko_list):
        out = root / "kofam"
        out.mkdir()
        (out / "ids.txt").write_text("K3\nK1\n")
        build_mini_dbs.main(
            [
                "kofam",
                "--profiles",
                str(profiles),
                "--ko-list",
                str(ko_list),
                "--out",
                str(out),
            ]
        )
        return (out / "kofam.hmm").read_text(), (out / "kofam_ko_list.tsv").read_text()

    def test_builds_listed_kos_from_genomenet_release_in_ids_order(self):
        # ids.txt records the full database's model order, which hit lists such as
        # kofam_ids follow; the release tarball can't tell us that order.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profiles = root / "profiles.tar.gz"
            with tarfile.open(profiles, "w:gz") as tar:
                for name, length in [("K3", 30), ("K1", 10), ("K2", 20)]:
                    data = hmm_record(name, length).encode()
                    info = tarfile.TarInfo(f"profiles/{name}.hmm")
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
            ko_list = root / "ko_list.gz"
            ko_list.write_bytes(gzip.compress(KO_LIST.encode()))

            hmm, ko_rows = self.run_kofam(root, profiles, ko_list)

        self.assertEqual(hmm, hmm_record("K3", 30) + hmm_record("K1", 10))
        self.assertEqual(
            ko_rows,
            "knum\tthreshold\tscore_type\tdefinition\n"
            "K1\t10.0\tfull\tone\n"
            "K3\t30.0\tfull\tthree [EC:1.1.1.1]\n",
        )

    def test_local_concatenated_profiles_give_the_same_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profiles = root / "kofam_profiles.hmm"
            profiles.write_text(
                hmm_record("K1", 10) + hmm_record("K2", 20) + hmm_record("K3", 30)
            )
            ko_list = root / "kofam_ko_list.tsv"
            ko_list.write_text(KO_LIST)

            hmm, ko_rows = self.run_kofam(root, profiles, ko_list)

        self.assertEqual(hmm, hmm_record("K3", 30) + hmm_record("K1", 10))
        self.assertEqual(
            ko_rows.splitlines()[1:],
            ["K1\t10.0\tfull\tone", "K3\t30.0\tfull\tthree [EC:1.1.1.1]"],
        )
