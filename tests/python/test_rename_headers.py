import subprocess
import sys

import pytest

from conftest import BIN, GENOMES, OWC


def run_rename(tmp_path, *pairs):
    """rename_headers.py over NAME FASTA pairs; returns (outdir, manifest lines, stderr)."""
    outdir, manifest = tmp_path / "RENAMED_HEADERS", tmp_path / "manifest.tsv"
    done = subprocess.run(
        [sys.executable, BIN / "rename_headers.py", manifest, outdir, *pairs],
        check=True,
        capture_output=True,
        text=True,
    )
    return outdir, manifest.read_text().splitlines(), done.stderr


def test_prefixes_headers_with_genome(tmp_path):
    pairs = [x for g in GENOMES for x in (g, OWC / "input_fasta" / f"{g}.fa")]
    outdir, manifest, _ = run_rename(tmp_path, *pairs)
    assert manifest == [f"{g}\t{g}.fa" for g in GENOMES]
    for genome in GENOMES:
        out = outdir / f"{genome}.fa"
        assert not out.is_symlink()
        # the committed fixture wraps lines at a different width; compare records
        assert records(out) == records(OWC / "renamed_fasta" / f"{genome}.fa")


@pytest.mark.parametrize("genome", GENOMES)
def test_links_already_renamed_file_unchanged(tmp_path, genome):
    renamed = OWC / "renamed_fasta" / f"{genome}.fa"
    outdir, manifest, err = run_rename(tmp_path, genome, renamed)
    out = outdir / f"{genome}.fa"
    assert manifest == [f"{genome}\t{genome}.fa"]
    assert out.is_symlink()
    assert out.read_bytes() == renamed.read_bytes()
    assert "already renamed" in err


def test_partly_renamed_file_is_renamed_with_warning(tmp_path):
    fasta = tmp_path / "s.faa"
    fasta.write_text(">s_a\nMK\n>b\nMK\n")
    outdir, _, err = run_rename(tmp_path, "s", fasta)
    assert (outdir / "s.faa").read_text() == ">s_s_a\nMK\n>s_b\nMK\n"
    assert "WARNING" in err and "1 headers" in err


def test_name_prefix_needs_underscore(tmp_path):
    # bin10_ headers are not bin1's: starting with "bin1" alone is not Renamed
    fasta = tmp_path / "bin1.fa"
    fasta.write_text(">bin10_c1\nACGT\n")
    outdir, _, err = run_rename(tmp_path, "bin1", fasta)
    out = outdir / "bin1.fa"
    assert not out.is_symlink()
    assert out.read_text() == ">bin1_bin10_c1\nACGT\n"
    assert not err


def records(path):
    """{header: sequence}, ignoring line wrapping."""
    text = path.read_text()
    return {
        r.split("\n", 1)[0]: r.split("\n", 1)[1].replace("\n", "")
        for r in text.lstrip(">").split("\n>")
    }
