"""Documentation must agree with validation/metrics.json and must not speculate about hidden results."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "validation" / "metrics.json").read_text(encoding="utf-8"))
EXP = json.loads((ROOT / "validation" / "experiments.json").read_text(encoding="utf-8"))
DOCS = ["README.md", "memo.md", "submission-form.md", "validation/validation_report.md"]
USER_FACING = DOCS + ["app.py", "RECORDING_GUIDE.md", "SECURITY.md", "validation/experiment_report.md"]

def text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")

def expected_strings() -> list[str]:
    q = M
    return [f"{q['roc_auc']:.4f}", f"{q['avg_precision']:.4f}", f"{q['accuracy_at_0.5']:.4%}",
            f"{q['queue_fraud']}", f"{q['queue_reviewed']}", f"{q['queue_fraud_value_inr']:,.0f}",
            f"{q['fraud_value_per_review_inr']:,.2f}", f"{q['residual_after_goodwill_inr']:,.0f}",
            f"{q['residual_per_review_inr']:.2f}", f"{q['labeled_rows']:,}", f"{q['fraud_rows']}"]

@pytest.mark.parametrize("doc", ["README.md", "memo.md", "submission-form.md"])
def test_docs_quote_the_verified_metrics(doc):
    t = text(doc)
    assert [s for s in expected_strings() if s not in t] == []

def test_validation_report_matches_metrics_json_exactly():
    from src.validate import render_report
    assert text("validation/validation_report.md").strip() == render_report(M).strip()

def test_monthly_and_bootstrap_numbers_in_readme():
    t = text("README.md")
    for x in M["monthly"].values():
        assert f"{x['roc_auc']:.4f}" in t
    b = M["bootstrap_auc"]
    assert f"{b['ci_low']:.3f}-{b['ci_high']:.3f}" in t and str(b["n_resamples"]).replace("000", ",000") in t

def test_memo_experiment_numbers_match_experiments_json():
    t = text("memo.md")
    dev = EXP["development_Oct2025_Mar2026"]
    assert f"{dev['A_current']['roc_auc']:.3f}" in t
    assert f"{dev['ablations']['remove_partner_history']['roc_auc']:.3f}" in t
    assert f"{EXP['validation_Apr_Jun2026']['ablations']['remove_partner_history']['roc_auc']:.4f}" in t

def test_production_model_unchanged_by_experiments():
    cfg = json.loads((ROOT / "src" / "model_config.json").read_text(encoding="utf-8"))["formula"]
    assert cfg["partner_rate_weight"] == 0.75 and cfg["recent_partner_rate_weight"] == 0.15

@pytest.mark.parametrize("doc", USER_FACING + ["validation/metrics.json"])
def test_no_old_draft_metrics_in_user_facing_files(doc):
    t = text(doc)
    for draft in ("0.8368", "0.1542", "97.8918"):
        assert draft not in t, (doc, draft)

@pytest.mark.parametrize("doc", USER_FACING)
def test_no_speculative_hidden_test_estimates(doc):
    t = text(doc).lower()
    for pattern in (r"0\.75\s*-\s*0\.91", r"97\s*-\s*98\s*%", r"about 0\.83", r"expect(ed)? (roughly|to score|a hidden)",
                    r"plausible range", r"estimate, not a result", r"hidden[- ]test (roc|auc|accuracy) (of|will)"):
        assert not re.search(pattern, t), (doc, pattern)

@pytest.mark.parametrize("doc", ["README.md", "memo.md", "app.py", "validation/validation_report.md"])
def test_hidden_outcomes_unavailable_statement_present(doc):
    assert "hidden-test performance has not been measured" in text(doc)

def test_form_hidden_estimate_is_labelled_not_measured_and_tied_to_backtest():
    t = text("submission-form.md")
    assert "has not been measured" in t and "estimate only" in t and "approximately 0.80" in t
    assert f"{M['roc_auc']:.4f}" in t and "approximately 0.745-0.908" in t
    assert not re.search(r"(achieved|scored|measured)( a)? (roc-auc )?(of )?0\.80", t.lower())

@pytest.mark.parametrize("doc", ["README.md", "memo.md", "submission-form.md", "validation/validation_report.md"])
def test_economic_caveat_is_present_and_careful(doc):
    t = text(doc)
    assert "gross" in t.lower() and "713" in t and "before investigator time" in t
    affirmative = [x for x in re.split(r"[.\n]", t.lower()) if " not " not in f" {x} " and "n't" not in x]
    assert not [x for x in affirmative if re.search(r"guaranteed savings|proven roi|is profitable|will save|net benefit of", x)]

@pytest.mark.parametrize("doc", USER_FACING)
def test_score_is_never_described_as_a_probability(doc):
    for sentence in re.split(r"[.\n]", text(doc).lower()):
        if re.search(r"probab", sentence):
            assert re.search(r"\bnot\b|no hidden|n't|never|predicted score", sentence), (doc, sentence.strip())
    assert not re.search(r"(fraud probability|probability of fraud|% chance|likelihood of fraud)", text(doc).lower())

def test_onboarding_check_recorded_and_clean():
    c = M["onboarding_date_check"]
    assert c["claims_checked"] == M["labeled_rows"] and c["onboarded_after_claim"] == 0

def test_experiment_report_explanation_matches_json():
    t = text("validation/experiment_report.md")
    d = EXP["development_Oct2025_Mar2026"]["ablations"]["remove_partner_history"]["roc_auc"]
    assert f"{d:.3f}" in t and "not retuned solely on that period" in t and "optimal" in t
