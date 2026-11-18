"""REFINE and COMBINE_ANNOTATIONS run dram-rules on REFINE's environment, so
it must hold every dram-rules dependency with dram-rules' bound."""

import re
import tomllib

from conftest import ROOT
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

RULES_PYPROJECT = ROOT / "bin/rules/pyproject.toml"
REFINE_ENV = ROOT / "modules/local/refine/environment.yml"
FIX = (
    "Set the same bound in modules/local/refine/environment.yml, then rebuild its "
    "images with wave and update the container lines (docs/contributing.md)."
)


def env_dependencies():
    """{name: the rest of the line} for the conda environment's dependencies."""
    lines = re.findall(r"^\s*-\s*([^#\n]+)", REFINE_ENV.read_text(), re.M)
    return dict(re.match(r"([\w.-]+)\s*(.*?)\s*$", d).groups() for d in lines)


def test_refine_env_has_dram_rules_dependencies():
    project = tomllib.loads(RULES_PYPROJECT.read_text())["project"]
    env = env_dependencies()
    for dependency in map(Requirement, project["dependencies"]):
        assert dependency.name in env, f"{dependency.name} is missing. {FIX}"
        got = SpecifierSet(env[dependency.name])
        assert got == dependency.specifier, (
            f"{dependency.name}: {got} here, {dependency.specifier} in dram-rules. {FIX}"
        )
    python = env["python"].removeprefix("=")
    assert SpecifierSet(project["requires-python"]).contains(python), FIX
