"""Development experiments on the SAME chronological validation as src.validate.

  A  current production model
  B  A + policy-aware claim-amount indicators (fixed, documented weights; nothing fitted on validation outcomes)
  ablations: remove one signal at a time (weight set to 0)

Writes validation/experiments.json and validation/experiment_report.md.
Run:  python -m src.experiments     (needs data/train.csv and data/partners.csv)
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.paths import DATA, ROOT, require
from src.scorer import AUTO_APPROVAL_FROM, SMALL_CLAIM_LIMIT_INR, score_claim
from src.train import prepare_labeled
from src.validate import BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, MONTHS, summarize, walk_forward_scores

OUT_JSON = ROOT / "validation" / "experiments.json"
OUT_MD = ROOT / "validation" / "experiment_report.md"
ABLATIONS = {
    "remove_partner_history": "partner_rate_weight",
    "remove_recent_partner_rate": "recent_partner_rate_weight",
    "remove_partner_recency": "new_partner_weight",
    "remove_customer_prior_claims": "prior_claims_weight",
    "remove_inspection_signal": "uninspected_weight",
}
B_WEIGHTS = (0.02, 0.05, 0.10)

def _zero(weight_key: str):
    def mut(cfg: dict) -> dict:
        cfg["formula"][weight_key] = 0.0
        return cfg
    return mut

def _amount_features(record: dict) -> tuple[float, float]:
    """(small_claim, small_claim_after_1_May_2026) using only fields known when the claim arrives."""
    amount = pd.to_numeric(record.get("claim_amount_inr"), errors="coerce")
    ts = pd.Timestamp(record["submitted_at"])
    small = float(pd.notna(amount) and amount < SMALL_CLAIM_LIMIT_INR)
    return small, float(small and ts >= AUTO_APPROVAL_FROM)

def model_b(weight: float):
    def fn(record: dict, cfg: dict) -> float:
        small, small_post = _amount_features(record)
        return float(min(1.0, score_claim(record, cfg)["score"] + weight * small_post + 0.0 * small))
    return fn

def model_b_amount_band(weight: float):
    def fn(record: dict, cfg: dict) -> float:
        small, _ = _amount_features(record)
        return float(min(1.0, score_claim(record, cfg)["score"] + weight * small))
    return fn

def _row(v: pd.DataFrame) -> dict:
    s = summarize(v)
    return {k: s[k] for k in ("roc_auc", "avg_precision", "accuracy_at_0.5", "queue_fraud", "queue_reviewed",
                              "queue_fraud_value_inr", "fraud_value_per_review_inr")} | {
        "monthly_roc_auc": {m: x["roc_auc"] for m, x in s["monthly"].items()}}

def paired_bootstrap_auc_diff(y, a, b, n=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED) -> dict:
    rng = np.random.default_rng(seed)
    d = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            d.append(roc_auc_score(y[i], b[i]) - roc_auc_score(y[i], a[i]))
    lo, hi = np.percentile(d, [2.5, 97.5])
    return {"mean_diff": float(np.mean(d)), "ci_low": float(lo), "ci_high": float(hi), "resamples": n, "seed": seed}

DEV_MONTHS = [("2025-10-01", "2025-11-01"), ("2025-11-01", "2025-12-01"), ("2025-12-01", "2026-01-01"),
              ("2026-01-01", "2026-02-01"), ("2026-02-01", "2026-03-01"), ("2026-03-01", "2026-04-01")]
WINDOWS = {"development_Oct2025_Mar2026": DEV_MONTHS, "validation_Apr_Jun2026": MONTHS}
WEIGHT_GRID = [(0.75, 0.15), (0.5, 0.15), (0.25, 0.15), (0.0, 0.15), (0.25, 0.5)]   # (historical, recent) partner weights

def _weights(hist: float, recent: float):
    def mut(cfg: dict) -> dict:
        cfg["formula"]["partner_rate_weight"] = hist
        cfg["formula"]["recent_partner_rate_weight"] = recent
        return cfg
    return mut

def _window(lab, partners, months) -> dict:
    va = walk_forward_scores(lab, partners, months)
    y = va.is_fraud.values
    out = {"months": [m[0][:7] for m in months], "val_rows": int(len(va)), "val_fraud": int(y.sum()),
           "A_current": _row(va), "B_policy_aware_amount": {}, "B_amount_band_only": {}, "ablations": {},
           "contributions": {}, "partner_weight_grid": {}}
    for w in B_WEIGHTS:
        vb = walk_forward_scores(lab, partners, months, score_fn=model_b(w))
        out["B_policy_aware_amount"][str(w)] = _row(vb) | {
            "auc_diff_vs_A": paired_bootstrap_auc_diff(y, va.score.values, vb.score.values)}
        vc = walk_forward_scores(lab, partners, months, score_fn=model_b_amount_band(w))
        out["B_amount_band_only"][str(w)] = _row(vc) | {
            "auc_diff_vs_A": paired_bootstrap_auc_diff(y, va.score.values, vc.score.values)}
    for name, key in ABLATIONS.items():
        vx = walk_forward_scores(lab, partners, months, cfg_mutator=_zero(key))
        out["ablations"][name] = _row(vx)
        delta = va.score.values - vx.score.values
        out["contributions"][name] = {"mean_points": float(delta.mean()), "std_points": float(delta.std())}
    tot = sum(c["std_points"] for c in out["contributions"].values())
    for c in out["contributions"].values():
        c["share_of_score_spread"] = c["std_points"] / tot
    for h, r in WEIGHT_GRID:
        out["partner_weight_grid"][f"hist={h},recent={r}"] = _row(
            walk_forward_scores(lab, partners, months, cfg_mutator=_weights(h, r)))
    seg = va.assign(small=va.claim_amount_inr < SMALL_CLAIM_LIMIT_INR, post=va.submitted_dt >= AUTO_APPROVAL_FROM)
    out["small_claims_by_period"] = {f"post_1_May_2026={bool(p)}": {"claims": int(len(g)), "fraud": int(g.is_fraud.sum())}
                                     for (p,), g in seg[seg.small].groupby(["post"])}
    return out

def run(data_dir=DATA) -> dict:
    require(["train.csv", "partners.csv"], data_dir)
    partners = pd.read_csv(data_dir / "partners.csv")
    lab = prepare_labeled(pd.read_csv(data_dir / "train.csv"))
    return {name: _window(lab, partners, months) for name, months in WINDOWS.items()}

def _pct(x): return "n/a" if x is None else f"{x:.4f}"

def _line(name, d):
    mo = " / ".join(_pct(v) for v in d["monthly_roc_auc"].values())
    return (f"| {name} | {d['roc_auc']:.4f} | {d['avg_precision']:.4f} | {d['accuracy_at_0.5']:.4%} | {mo} | "
            f"{d['queue_fraud']}/{d['queue_reviewed']} | Rs {d['queue_fraud_value_inr']:,.0f} | Rs {d['fraud_value_per_review_inr']:,.2f} |")

HEAD = ("| Variant | ROC-AUC | Avg precision | Accuracy @0.5 | Monthly ROC-AUC | Top-40 fraud | Fraud value | Gross value per review |\n"
        "|---|---|---|---|---|---|---|---|")

def render(res: dict) -> str:
    out = ["# Development experiments (same walk-forward protocol as `python -m src.validate`)", "",
           "Reproduce with `python -m src.experiments` (private data required). Historical results only; no hidden-test claim.",
           "The development window (Oct 2025 - Mar 2026) is used only to check whether a finding in the validation window "
           "(Apr - Jun 2026) is stable. B weights are fixed, documented values, not fitted on outcomes.", ""]
    for name, r in res.items():
        out += [f"## Window: {name} ({r['val_rows']:,} claims, {r['val_fraud']} fraud)", "", "### Claim-amount experiment (A vs B)", HEAD,
                _line("A: current production model", r["A_current"])]
        out += [_line(f"B: A + small-claim-after-1-May indicator, +{w}", d) for w, d in r["B_policy_aware_amount"].items()]
        out += [_line(f"B': A + small-claim indicator (any date), +{w}", d) for w, d in r["B_amount_band_only"].items()]
        out += ["", "Paired bootstrap ROC-AUC difference vs A (95% interval):"]
        for key, label in (("B_policy_aware_amount", "B"), ("B_amount_band_only", "B'")):
            for w, d in r[key].items():
                x = d["auc_diff_vs_A"]
                out.append(f"- {label} +{w}: {x['mean_diff']:+.4f} ({x['ci_low']:+.4f} to {x['ci_high']:+.4f})")
        out += ["", f"Small claims (< Rs 2,000) by period: {json.dumps(r['small_claims_by_period'])}", "",
                "### Ablation: one signal removed (weight 0)", HEAD]
        out += [_line(n, d) for n, d in r["ablations"].items()]
        out += ["", "### Partner-weight sensitivity (historical weight, recent weight)", HEAD]
        out += [_line(n, d) for n, d in r["partner_weight_grid"].items()]
        out += ["", "### Signal contributions in the current score", "| Signal | Mean (score points) | Std | Share of score spread |", "|---|---|---|---|"]
        out += [f"| {n} | {c['mean_points']:.4f} | {c['std_points']:.4f} | {c['share_of_score_spread']:.1%} |"
                for n, c in r["contributions"].items()]
        out.append("")
    dev, val = res["development_Oct2025_Mar2026"], res["validation_Apr_Jun2026"]
    d0, d1 = dev["A_current"], dev["ablations"]["remove_partner_history"]
    v0, v1 = val["A_current"], val["ablations"]["remove_partner_history"]
    apr0, apr1 = list(v0["monthly_roc_auc"].values())[0], list(v1["monthly_roc_auc"].values())[0]
    out += ["## How to read the partner-history results", "",
            f"Partner history was useful in the earlier development period (removing it cut ROC-AUC from {d0['roc_auc']:.3f} to "
            f"{d1['roc_auc']:.3f} and top-40 hits from {d0['queue_fraud']} to {d1['queue_fraud']} of {d0['queue_reviewed']}) but became "
            f"less consistent after May 2026: in Apr-Jun 2026 removing it left ROC-AUC essentially unchanged ({v0['roc_auc']:.4f} to "
            f"{v1['roc_auc']:.4f}) and raised average precision ({v0['avg_precision']:.4f} to {v1['avg_precision']:.4f}) and top-40 hits "
            f"({v0['queue_fraud']} to {v1['queue_fraud']}), although April ranked worse without it ({apr0:.3f} to {apr1:.3f}) while May "
            f"and June ranked better. The post-May validation sample is still small ({val['val_fraud']} fraud cases across Apr-Jun), so the "
            "existing model was not retuned solely on that period. Partner-history behaviour should be monitored as more post-May outcomes "
            "become available. These results do not show that partner history is optimal, nor that it is definitely necessary.", ""]
    return "\n".join(out)

if __name__ == "__main__":
    try:
        res = run()
    except FileNotFoundError as e:
        raise SystemExit(f"ERROR: {e}")
    OUT_JSON.write_text(json.dumps(res, indent=2), encoding="utf-8")
    OUT_MD.write_text(render(res), encoding="utf-8")
    print(render(res))
