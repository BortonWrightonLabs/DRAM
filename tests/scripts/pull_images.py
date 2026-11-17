#!/usr/bin/env python
"""Pull the apptainer images a pipeline uses into Nextflow's image cache, with retries.

Nextflow doesn't retry a failed image download (errorStrategy never runs), so one
dropped connection fails the run. Pulling first, with retries, into the directory
Nextflow reads (NXF_APPTAINER_CACHEDIR) means the run itself downloads nothing.

    nextflow inspect main.nf -profile test,apptainer ... > images.json
    pull_images.py images.json CACHE_DIR
"""

import json
import subprocess
import sys
import time
from pathlib import Path

REGISTRY = "quay.io"  # apptainer.registry in nextflow.config
WAITS = [10, 30, 60]  # seconds before each retry


def image_url(container):
    """The URL Nextflow pulls: bare names get docker:// and, without a registry host, REGISTRY."""
    if "://" in container:
        return container
    host = container.split("/")[0]
    if "." in host or ":" in host or host == "localhost":
        return f"docker://{container}"
    return f"docker://{REGISTRY}/{container}"


def cache_name(url):
    """Nextflow's file name for an image in its cache."""
    return url.split("://", 1)[1].replace(":", "-").replace("/", "-") + ".img"


def pull(url, path):
    partial = path.with_name(path.name + ".pulling")
    for attempt, wait in enumerate([0, *WAITS]):
        time.sleep(wait)
        partial.unlink(missing_ok=True)
        result = subprocess.run(["apptainer", "pull", "--force", partial, url])
        if result.returncode == 0:
            partial.rename(path)
            return
        print(f"pull failed ({attempt + 1}/{len(WAITS) + 1}): {url}", file=sys.stderr)
    raise SystemExit(f"could not pull {url}")


def main(inspect_json, cache_dir):
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    processes = json.loads(Path(inspect_json).read_text())["processes"]
    for url in sorted(
        {image_url(p["container"]) for p in processes if p.get("container")}
    ):
        path = cache_dir / cache_name(url)
        if not path.exists():
            pull(url, path)


if __name__ == "__main__":
    main(*sys.argv[1:])
