"""Streamlit smoke tests (scripted UI run; no browser, no private data needed)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")

@pytest.fixture
def at(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:9")   # nothing listens here: exercises the 'API stopped' path
    return AppTest.from_file(APP, default_timeout=30).run()

def _click(app, label):
    [b for b in app.button if b.label == label][0].click()
    return app.run()

def test_loads_with_five_tabs_and_review_priority_warning(at):
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Overview & data status", "Score a claim", "API test", "Review queue", "Model & validation"]
    assert any("review-priority" in w.value.lower() and "does not decide" in w.value.lower() for w in at.warning)

def test_score_safe_example_shows_reasons_and_level(at):
    at = _click(at, "Score claim")
    assert not at.exception and not at.error
    labels = {m.label: m.value for m in at.metric}
    assert {"Review-priority score", "Risk level"} <= set(labels) and "As percentage" not in labels
    assert any(m.value.startswith("- ") or "partner" in m.value.lower() for m in at.markdown)

def test_invalid_claim_shows_friendly_error_not_traceback(at):
    at.text_input(key="s_t").set_value("garbage")
    at = _click(at, "Score claim")
    assert not at.exception and any("Invalid claim" in e.value for e in at.error)

def test_stopped_api_is_handled_gracefully(at):
    at = _click(at, "Check API health")
    assert not at.exception and any("API not reachable" in e.value for e in at.error)
    at = _click(at, "Send to API")
    assert not at.exception and any("API not reachable" in e.value for e in at.error)

def test_model_tab_shows_final_metrics_only(at):
    import json
    m = json.loads((Path(APP).parent / "validation" / "metrics.json").read_text(encoding="utf-8"))
    shown = " ".join([x.label for x in at.metric] + [x.value for x in at.metric] + [x.value for x in at.markdown] + [x.value for x in at.caption]
                     + [x.value for x in at.warning] + [x.value for x in at.info])
    for needle in (f"{m['roc_auc']:.4f}", f"{m['avg_precision']:.4f}", f"{m['accuracy_at_0.5']:.4%}",
                   f"{m['queue_fraud_value_inr']:,.0f}", f"{m['fraud_value_per_review_inr']:,.2f}", f"{m['residual_after_goodwill_inr']:,.0f}"):
        assert needle in shown
    assert "gross" in shown.lower() and "hidden-test performance has not been measured" in shown
    assert not any(old in shown for old in ("0.8368", "0.1542", "97.8918"))
