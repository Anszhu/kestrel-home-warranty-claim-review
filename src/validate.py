"""Chronological (walk-forward) validation, Apr-Jun 2026 -> validation/metrics.json (+ validation_report.md).

For each validation month, partner statistics are fitted ONLY on labeled claims submitted
before that month starts (enforced by train.fit_config / assert_no_future).
Every statistic quoted in the documentation is produced here.
Run:  python -m src.validate     (needs data/train.csv and data/partners.csv)
"""
from __future__ import annotations

import copy
import json
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, average_precision_score, roc_auc_score

from src.paths import DATA, METRICS, ROOT, require
from src.scorer import score_claim
from src.train import LeakageError, assert_no_future, fit_config, onboarding_check, prepare_labeled

MONTHS = [("2026-04-01", "2026-05-01"), ("2026-05-01", "2026-06-01"), ("2026-06-01", "2026-07-01")]
CAPACITY_PER_MONTH = 40            # investigation desk capacity (ops policy s5)
GOODWILL_PER_HELD_CLAIM_INR = 380  # ops policy s4
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 42
REPORT = ROOT / "validation" / "validation_report.md"

ScoreFn = Callable[[dict, dict], float]

def default_score(record: dict, cfg: dict) -> float:
    return score_claim(record, cfg)["score"]

def walk_forward_scores(lab: pd.DataFrame, partners: pd.DataFrame, months=MONTHS,
                        score_fn: ScoreFn = default_score, cfg_mutator=None) -> pd.DataFrame:
    """Score each validation month with statistics fitted only on earlier claims."""
    parts = []
    for start, end in months:
        s, e = pd.Timestamp(start), pd.Timestamp(end)
        val = lab[(lab.submitted_dt >= s) & (lab.submitted_dt < e)].copy()
        cfg = fit_config(lab, partners, as_of=s)             # history strictly before the month
        assert_no_future(lab[lab.submitted_dt < s], val.submitted_dt.min())
        if cfg_mutator:
            cfg = cfg_mutator(copy.deepcopy(cfg))
        val["score"] = [score_fn(r, cfg) for r in val.to_dict("records")]
        val["month"] = start[:7]
        parts.append(val)
    return pd.concat(parts)

def _auc(y, s) -> float | None:
    return float(roc_auc_score(y, s)) if len(set(y)) == 2 else None

def bootstrap_auc(y: np.ndarray, s: np.ndarray, n: int = BOOTSTRAP_RESAMPLES, seed: int = BOOTSTRAP_SEED) -> dict:
    """Percentile bootstrap of ROC-AUC over validation claims (resamples without both classes are skipped)."""
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            vals.append(roc_auc_score(y[i], s[i]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return {"n_resamples": n, "valid_resamples": len(vals), "seed": seed,
            "ci_low": float(lo), "ci_high": float(hi)}

def summarize(v: pd.DataFrame, capacity: int = CAPACITY_PER_MONTH) -> dict:
    """Overall, monthly and top-`capacity`-per-month statistics for scored validation claims."""
    q = v.sort_values("score", ascending=False).groupby("month").head(capacity)
    fq = q[q.is_fraud == 1]
    n_genuine = len(q) - len(fq)
    fraud_value = float(fq.claim_amount_inr.sum())
    goodwill = float(n_genuine * GOODWILL_PER_HELD_CLAIM_INR)
    total_fraud_value = float(v[v.is_fraud == 1].claim_amount_inr.sum())
    monthly = {}
    for m, g in v.groupby("month"):
        a = _auc(g.is_fraud.values, g.score.values)
        monthly[m] = {"rows": int(len(g)), "fraud": int(g.is_fraud.sum()), "roc_auc": a,
                      "roc_auc_note": None if a is not None else "not defined: only one class in this month"}
    return {
        "val_rows": int(len(v)), "val_fraud": int(v.is_fraud.sum()),
        "roc_auc": _auc(v.is_fraud.values, v.score.values),
        "avg_precision": float(average_precision_score(v.is_fraud, v.score)),
        "accuracy_at_0.5": float(accuracy_score(v.is_fraud, v.score >= 0.5)),
        "all_genuine_accuracy": float(1 - v.is_fraud.mean()),
        "monthly": monthly,
        "queue_reviewed": int(len(q)), "queue_fraud": int(len(fq)),
        "queue_fraud_value_inr": fraud_value,
        "fraud_value_per_review_inr": fraud_value / len(q),
        "val_total_fraud_value_inr": total_fraud_value,
        "random_review_fraud_value_per_review_inr": total_fraud_value / len(v),
        "genuine_in_queue": int(n_genuine),
        "goodwill_if_all_genuine_held_inr": goodwill,
        "residual_after_goodwill_inr": fraud_value - goodwill,
        "residual_per_review_inr": (fraud_value - goodwill) / len(q),
    }

def run(data_dir=DATA, months=MONTHS, capacity: int = CAPACITY_PER_MONTH) -> dict:
    require(["train.csv", "partners.csv"], data_dir)
    partners = pd.read_csv(data_dir / "partners.csv")
    lab = prepare_labeled(pd.read_csv(data_dir / "train.csv"))
    check = onboarding_check(lab, partners)
    if check["onboarded_after_claim"]:
        raise LeakageError(f"{check['onboarded_after_claim']} claims precede their partner's onboarding date")
    v = walk_forward_scores(lab, partners, months)
    m = {"onboarding_date_check": check, "labeled_rows": int(len(lab)), "fraud_rows": int(lab.is_fraud.sum()),
         "fraud_prevalence": float(lab.is_fraud.mean())}
    m.update(summarize(v, capacity))
    m["bootstrap_auc"] = bootstrap_auc(v.is_fraud.values, v.score.values)
    return m

def render_report(m: dict) -> str:
    mo = "\n".join(f"| {k} | {x['rows']} | {x['fraud']} | "
                   f"{('%.4f' % x['roc_auc']) if x['roc_auc'] is not None else x['roc_auc_note']} |"
                   for k, x in m["monthly"].items())
    b = m["bootstrap_auc"]
    return f"""# Validation report (historical backtest, NOT hidden-test performance)

Hidden-test outcomes are unavailable, so hidden-test performance has not been measured. The strongest evidence is the
chronological Apr-Jun 2026 backtest below. Every number here is produced by `python -m src.validate` and stored in
`validation/metrics.json` (single source of truth).

## Protocol
Walk-forward by month. For each of Apr, May, Jun 2026 the partner statistics are fitted only on labeled claims submitted
before that month starts (`fit_config(..., as_of=...)` + `assert_no_future`; tests poison future rows to prove it).
Blank (undecided) outcomes are excluded; duplicate claim IDs are de-duplicated keeping the first copy.
Partner onboarding dates are static attributes; the check below confirms no labeled claim precedes its partner's onboarding date
(claims checked: {m['onboarding_date_check']['claims_checked']:,}; onboarded after the claim: {m['onboarding_date_check']['onboarded_after_claim']}; missing or invalid date: {m['onboarding_date_check']['missing_or_invalid_onboarding_date']}).

- Labeled rows: {m['labeled_rows']:,}; fraud rows: {m['fraud_rows']} ({m['fraud_prevalence']:.3%})
- Validation rows Apr-Jun 2026: {m['val_rows']:,} ({m['val_fraud']} fraud)

## Ranking and accuracy
| Metric | Value |
|---|---|
| ROC-AUC | {m['roc_auc']:.4f} |
| Average precision | {m['avg_precision']:.4f} |
| Accuracy at 0.5 | {m['accuracy_at_0.5']:.4%} (all-genuine baseline: {m['all_genuine_accuracy']:.4%}; the score never reaches 0.5) |
| Bootstrap 95% interval for ROC-AUC | {b['ci_low']:.3f} - {b['ci_high']:.3f} ({b['n_resamples']:,} resamples of validation claims, seed {b['seed']}) |

| Month | Claims | Fraud | ROC-AUC |
|---|---|---|---|
{mo}

## Top-{CAPACITY_PER_MONTH}-per-month review queue
- Fraud found: **{m['queue_fraud']} fraud / {m['queue_reviewed']} reviewed**
- Gross fraud value in the queue: **Rs {m['queue_fraud_value_inr']:,.0f}**; per review: **Rs {m['fraud_value_per_review_inr']:,.2f}**. This is the gross value of fraudulent claims surfaced per review in the validation queue (claim amounts of confirmed fraud); it is not savings, net benefit, ROI, profit or realised value. Reviewing at random would surface about Rs {m['random_review_fraud_value_per_review_inr']:,.2f} per review.
- Economic caveat: {m['genuine_in_queue']} of the {m['queue_reviewed']} reviewed claims were genuine. At Rs {GOODWILL_PER_HELD_CLAIM_INR} goodwill per genuine reviewed claim (policy s4, assuming each is held) that is Rs {m['goodwill_if_all_genuine_held_inr']:,.0f}. Illustrative residual after this goodwill assumption is approximately **Rs {m['residual_after_goodwill_inr']:,.0f}** across the historical validation queue (about Rs {m['residual_per_review_inr']:.2f} per review), before investigator time, the Rs 260 service-contact cost and other operational costs (none of which are included). This is not guaranteed savings, not a proven ROI, and not evidence that the model is profitable.
- The queue is the top {CAPACITY_PER_MONTH} claims per calendar month ranked with full-month visibility; an operational queue would be built as claims arrive.

## Limitations
Scores are review-priority rankings, not calibrated probabilities. Only {m['val_fraud']} fraud cases in the validation window, so all figures are noisy and month-to-month ranking quality varies; accuracy at 0.5 equals the all-genuine baseline; claim amount is not in the score; some legacy "genuine" labels may really be undecided cases.
"""

if __name__ == "__main__":
    try:
        m = run()
    except FileNotFoundError as e:
        raise SystemExit(f"ERROR: {e}")
    m["protocol"] = "walk-forward Apr-Jun 2026; partner stats fitted only on claims before each month"
    m["assumptions"] = ("Queue = top 40 per calendar month by score, ranked with full-month visibility. Fraud value = "
                        "claim_amount_inr of confirmed fraud in the queue (gross). Goodwill assumes every genuine reviewed "
                        "claim is held (Rs 380, policy s4); Rs 260 service-contact cost and investigator time not included.")
    METRICS.write_text(json.dumps(m, indent=2), encoding="utf-8")
    REPORT.write_text(render_report(m), encoding="utf-8")
    print(render_report(m))
