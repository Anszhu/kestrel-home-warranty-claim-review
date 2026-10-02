"""Pipeline tests on SYNTHETIC TEST DATA - NOT KESTREL DATA."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src import predict, train, validate
from src.paths import MissingDataError, missing_files, require

def _write_synthetic(d, n=600):
    rng = np.random.default_rng(0)
    ts = pd.date_range("2025-04-01", periods=n, freq="6h")
    pd.DataFrame({
        "claim_id": [f"SYN{i}" for i in range(n)], "submitted_at": ts.astype(str),
        "partner_id": rng.choice(["P1", "P2", "P3"], n), "customer_prior_claims": rng.integers(0, 3, n),
        "partner_inspected": "Y", "claim_amount_inr": rng.integers(500, 6000, n),
        "is_fraud": rng.choice([0.0, 1.0], n, p=[.9, .1]),
    }).to_csv(d / "train.csv", index=False)
    pd.DataFrame({"claim_id": ["T1", "T2"], "submitted_at": ["2026-07-01 10:00"] * 2, "partner_id": ["P1", "P9"],
                  "customer_prior_claims": [0, 2], "partner_inspected": ["Y", "N"]}).to_csv(d / "test_unlabelled.csv", index=False)
    pd.DataFrame({"claim_id": ["T1", "T2"], "score": [0, 0]}).to_csv(d / "sample_submission.csv", index=False)
    pd.DataFrame({"partner_id": ["P1", "P2", "P3"], "onboarded_date": ["2020-01-01"] * 3}).to_csv(d / "partners.csv", index=False)

@pytest.fixture
def syn(tmp_path):
    _write_synthetic(tmp_path)
    return tmp_path

def test_missing_data_messages_are_helpful_and_path_free(tmp_path):
    assert set(missing_files(tmp_path)) == {"train.csv", "test_unlabelled.csv", "partners.csv", "products.csv"}
    for fn in (lambda: train.make_config(tmp_path, tmp_path / "c.json"), lambda: predict.run(tmp_path, tmp_path / "o"),
               lambda: validate.run(tmp_path)):
        with pytest.raises(MissingDataError) as e:
            fn()
        assert "data/" in str(e.value) and str(tmp_path) not in str(e.value)
    with pytest.raises(MissingDataError, match="test_unlabelled.csv"):
        require(["test_unlabelled.csv"], tmp_path)

def test_train_and_predict_output_shape(syn):
    cfg = train.make_config(syn, syn / "cfg.json")
    assert set(json.loads((syn / "cfg.json").read_text())["partner_rate"]) == {"P1", "P2", "P3"} and "products" not in cfg
    out = predict.run(syn, syn / "out", cfg)
    saved = pd.read_csv(syn / "out" / "predictions.csv")
    assert list(saved.columns) == ["claim_id", "score"] and list(saved.claim_id) == ["T1", "T2"]
    assert saved.score.between(0, 1).all() and not saved.score.isna().any() and len(out) == 2

def test_predict_rejects_wrong_sample_shape(syn):
    pd.DataFrame({"claim_id": ["T1"], "score": [0]}).to_csv(syn / "sample_submission.csv", index=False)
    with pytest.raises(AssertionError):
        predict.run(syn, syn / "out", train.fit_config(train.prepare_labeled(pd.read_csv(syn / "train.csv")), pd.read_csv(syn / "partners.csv")))

def test_prepare_labeled_excludes_undecided_and_keeps_first_duplicate():
    df = pd.DataFrame({"claim_id": ["A", "A", "B", "C"], "submitted_at": ["2026-01-01"] * 4,
                       "is_fraud": [1.0, 0.0, np.nan, 0.0], "partner_id": "P"})
    lab = train.prepare_labeled(df)
    assert list(lab.claim_id) == ["A", "C"] and lab.set_index("claim_id").is_fraud["A"] == 1.0   # B undecided dropped, first A kept

def test_future_outcomes_cannot_change_partner_statistics(syn):
    lab = train.prepare_labeled(pd.read_csv(syn / "train.csv"))
    partners = pd.read_csv(syn / "partners.csv")
    cut = pd.Timestamp("2025-06-01")
    base = train.fit_config(lab, partners, as_of=cut)
    future = lab[lab.submitted_dt >= cut].copy()
    future["partner_id"], future["is_fraud"] = "P1", 1.0           # poison: all-fraud future rows
    poisoned = train.fit_config(pd.concat([lab, future]), partners, as_of=cut)
    assert base == poisoned

def test_assert_no_future_raises():
    h = pd.DataFrame({"submitted_dt": pd.to_datetime(["2026-01-01", "2026-04-01"])})
    with pytest.raises(train.LeakageError):
        train.assert_no_future(h, pd.Timestamp("2026-04-01"))
    train.assert_no_future(h, pd.Timestamp("2026-04-02"))

def test_validate_runs_walk_forward_on_synthetic(syn):
    m = validate.run(syn, months=[("2025-06-01", "2025-07-01")], capacity=40)
    assert m["queue_reviewed"] == 40 and 0 <= m["roc_auc"] <= 1 and m["val_rows"] > 40
    assert m["genuine_in_queue"] + m["queue_fraud"] == m["queue_reviewed"]


def test_validate_reports_every_statistic_reproducibly(syn):
    kw = dict(months=[("2025-05-01", "2025-06-01"), ("2025-06-01", "2025-07-01")], capacity=40)
    m1, m2 = validate.run(syn, **kw), validate.run(syn, **kw)
    assert m1 == m2                                                  # fixed seed => identical, incl. bootstrap
    assert set(m1["monthly"]) == {"2025-05", "2025-06"} and all("roc_auc" in x for x in m1["monthly"].values())
    b = m1["bootstrap_auc"]
    assert b["n_resamples"] == validate.BOOTSTRAP_RESAMPLES and b["seed"] == validate.BOOTSTRAP_SEED
    assert 0 <= b["ci_low"] <= b["ci_high"] <= 1 and b["valid_resamples"] > 0
    assert m1["queue_reviewed"] == 80 and m1["residual_after_goodwill_inr"] == m1["queue_fraud_value_inr"] - 380 * m1["genuine_in_queue"]

def test_month_with_one_class_is_reported_honestly_not_invented():
    v2 = pd.DataFrame({"month": ["2026-04"] * 4 + ["2026-05"] * 4, "is_fraud": [0.0] * 4 + [1.0, 0.0, 0.0, 1.0],
                       "score": [.1, .2, .3, .4, .9, .1, .2, .8], "claim_amount_inr": [100] * 8})
    out = validate.summarize(v2)["monthly"]
    assert out["2026-04"]["roc_auc"] is None and "one class" in out["2026-04"]["roc_auc_note"]
    assert out["2026-05"]["roc_auc"] == 1.0

def test_prediction_is_deterministic_and_schema_exact(syn):
    cfg = train.make_config(syn, syn / "cfg.json")
    predict.run(syn, syn / "o1", cfg); predict.run(syn, syn / "o2", cfg)
    a, b = (syn / "o1" / "predictions.csv").read_bytes(), (syn / "o2" / "predictions.csv").read_bytes()
    assert a == b and a.splitlines()[0] == b"claim_id,score"

def test_onboarding_check_counts_future_onboarding_and_missing_dates():
    claims = pd.DataFrame({"partner_id": ["A", "B", "C", "Z"],
                           "submitted_dt": pd.to_datetime(["2026-01-10"] * 4)})
    partners = pd.DataFrame({"partner_id": ["A", "B", "C"], "onboarded_date": ["2025-01-01", "2026-02-01", "not-a-date"]})
    c = train.onboarding_check(claims, partners)
    assert c == {"claims_checked": 4, "onboarded_after_claim": 1, "missing_or_invalid_onboarding_date": 2}

def test_validate_refuses_claims_that_precede_partner_onboarding(syn):
    pd.DataFrame({"partner_id": ["P1", "P2", "P3"], "onboarded_date": ["2025-05-01", "2020-01-01", "2020-01-01"]}).to_csv(syn / "partners.csv", index=False)
    with pytest.raises(train.LeakageError, match="onboarding"):
        validate.run(syn, months=[("2025-06-01", "2025-07-01")])

@pytest.mark.skipif(not (Path(__file__).resolve().parents[1] / "data" / "train.csv").exists(), reason="private data not present")
def test_real_data_no_claim_precedes_partner_onboarding():
    d = Path(__file__).resolve().parents[1] / "data"
    lab = train.prepare_labeled(pd.read_csv(d / "train.csv"))
    c = train.onboarding_check(lab, pd.read_csv(d / "partners.csv"))
    assert c["onboarded_after_claim"] == 0 and c["missing_or_invalid_onboarding_date"] == 0
