"""COMBINE_ANNOTATIONS imports dram-rules, so its container's polars must fit
dram-rules' bound."""

from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[2]
RULES_PYPROJECT = ROOT / "bin/rules/pyproject.toml"
ANNOTATE_ENV = ROOT / "modules/local/annotate/environment.yml"


def bound(requirement):
    """'polars >=2,<3' -> '>=2,<3'."""
    return re.sub(r"\s", "", requirement).removeprefix("polars")


def test_annotate_env_polars_matches_dram_rules():
    rules = tomllib.loads(RULES_PYPROJECT.read_text())["project"]["dependencies"]
    (rules_polars,) = [d for d in rules if re.match(r"polars\b", d)]
    (env_polars,) = re.findall(r"^\s*-\s*(polars\b.*)$", ANNOTATE_ENV.read_text(), re.M)
    # On failure: set the same bound in both, then rebuild the annotate images
    # with wave and update the `container` lines of every module using them
    # (docs/contributing.md).
    assert bound(env_polars) == bound(rules_polars)
