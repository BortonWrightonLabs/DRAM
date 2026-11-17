"""tests/scripts/refine_values.py: the value comparator."""

import sys

from conftest import ROOT

sys.path.insert(0, str(ROOT / "tests/scripts"))
import refine_values  # noqa: E402

VERTICAL = "genome\tpresent\tname\tgene_ids_present\tlong_name\n"
VERTICAL += "g1\ttrue\taerobic\tK02275\taerobic\ng2\tfalse\taerobic\t\taerobic\n"
COVERAGE = "genome\tcoverage_percentage\tname\nn1\t0.5\tGlycolysis\ng2\t0\tGlycolysis\n"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_current_and_refine_layouts_give_the_same_values(tmp_path):
    today, refine = tmp_path / "today", tmp_path / "refine"
    write(
        today / "SUMMARIZE/summarized_genomes.tsv",
        "gene_id\tgene_description\ttopic_ecosystem\tmodule\tworkbook\tg2\tg1\n"
        "K00001\td\tEnergy\tm\tenergy_summary\t0\t2\n"
        "K00001\td\teng_sys\tm2\tecosystem_summary\t0\t2\n"
        "`Ala (CGC)`\tt\tHousekeeping\ttRNAs\tcell_summary\t1\t0\n",
    )
    write(today / "SUMMARIZE/df_vertical_genome.tsv", VERTICAL)
    write(today / "VISUALIZE/df_vertical_genome_ag.tsv", COVERAGE)
    # Refine: one table per Summary Collection, label column first, Groups as header/subheader
    write(
        refine / "summarize/topic_summary.tsv",
        "gene_id\tgene_description\tmodule\theader\tg1\tg2\nK00001\td\tm\tEnergy\t2\t0\n",
    )
    write(
        refine / "summarize/ecosystem_summary.tsv",
        "name\tmodule\tsubheader\tg1\tg2\nAla (CGC)\ttRNAs\tx\t0\t1\nK00001\tm2\tx\t2\t0\n",
    )
    write(refine / "traits/df_vertical_genome.tsv", VERTICAL)
    write(refine / "visualize/ag/df_vertical_genome.tsv", COVERAGE)

    values = refine_values.extract(today)
    assert values == refine_values.extract(refine)
    assert values == {
        ("gene_count", "", "K00001", "g1"): 2,
        ("gene_count", "", "Ala (CGC)", "g2"): 1,
        ("presence", "traits", "aerobic", "g1"): True,
        ("coverage", "visualize/ag", "Glycolysis", "n1"): 0.5,
    }


def test_values_round_trip_through_the_baseline_file(tmp_path):
    values = {
        ("gene_count", "", "K00001", "g1"): 2,
        ("presence", "traits", "aerobic", "g1"): True,
        ("coverage", "visualize/ag", "Glycolysis", "n1"): 0.5,
    }
    refine_values.write_values(values, tmp_path / "values.tsv")
    assert refine_values.read_values(tmp_path / "values.tsv") == values


def test_only_allowlisted_differences_pass():
    baseline = {
        ("gene_count", "", "K00001", "g1"): 2,
        ("gene_count", "", "K2", "g1"): 1,
    }
    actual = {("gene_count", "", "K00001", "g1"): 3, ("gene_count", "", "K2", "g1"): 1}
    diffs = refine_values.differences(actual, baseline)
    assert diffs == {("gene_count", "", "K00001", "g1"): (2, 3)}
    assert not refine_values.report(diffs, set())
    assert refine_values.report(diffs, {"gene_count||K00001|g1"})
    # an allowlisted difference that went away must be removed from the allowlist
    assert not refine_values.report(
        diffs, {"gene_count||K00001|g1", "gene_count||K2|g1"}
    )
