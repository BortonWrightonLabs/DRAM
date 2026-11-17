import subprocess
import sys

import pytest

from conftest import BIN, GENOMES, OWC


@pytest.mark.parametrize("genome", GENOMES)
def test_prefixes_headers_with_genome(tmp_path, genome):
    subprocess.run(
        [sys.executable, BIN / "rename_headers.py"]
        + [OWC / "input_fasta" / f"{genome}.fa", tmp_path, genome],
        check=True,
    )
    # the committed fixture wraps lines at a different width; compare records
    assert records(tmp_path / f"{genome}.fa") == records(
        OWC / "renamed_fasta" / f"{genome}.fa"
    )


def records(path):
    """{header: sequence}, ignoring line wrapping."""
    text = path.read_text()
    return {
        r.split("\n", 1)[0]: r.split("\n", 1)[1].replace("\n", "")
        for r in text.lstrip(">").split("\n>")
    }
