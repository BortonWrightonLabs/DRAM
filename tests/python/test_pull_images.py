"""tests/scripts/pull_images.py: image names must match Nextflow's cache, or the run re-downloads."""

import sys

from conftest import ROOT

sys.path.insert(0, str(ROOT / "tests/scripts"))
import pull_images  # noqa: E402


def test_cache_names_match_nextflow():
    # names Nextflow 25.10 wrote to NXF_APPTAINER_CACHEDIR for this pipeline's containers
    cases = {
        "oras://community.wave.seqera.io/library/bbmap:eecc2d5093684dba": "community.wave.seqera.io-library-bbmap-eecc2d5093684dba.img",
        "biocontainers/multiqc:1.25.1--pyhdfd78af_0": "quay.io-biocontainers-multiqc-1.25.1--pyhdfd78af_0.img",
    }
    for container, name in cases.items():
        assert pull_images.cache_name(pull_images.image_url(container)) == name
