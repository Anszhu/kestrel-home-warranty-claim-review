"""Fit the scoring configuration from the private labeled history -> src/model_config.json.

Run:  python -m src.train      (needs data/train.csv and data/partners.csv)

Data handling (documented decisions):
  * blank is_fraud = undecided at export -> excluded, never treated as genuine or fraud;
  * the same claim_id can appear twice (partner re-submissions) -> first row kept;
  * partner statistics use only claims submitted before `as_of` when one is given.
"""
from __future__ import annotations

import json

import pandas as pd

from src.paths import DATA, CFG, require

FORMULA = {
    "partner_rate_weight": 0.75,
    "recent_partner_rate_weight": 0.15,
    "new_partner_weight": 0.04,
    "prior_claims_weight": 0.04,
    "uninspected_weight": 0.02,
    "new_partner_days_threshold": 365,
}
SMOOTHING = 10          # pseudo-claims pulling small partners towards the portfolio rate
RECENT_DAYS = 90

class LeakageError(RuntimeError):
    """Raised when history contains claims on/after the boundary it must precede."""

def prepare_labeled(train: pd.DataFrame) -> pd.DataFrame:
    labeled = train.dropna(subset=["is_fraud"]).drop_duplicates("claim_id", keep="first").copy()
    labeled["submitted_dt"] = pd.to_datetime(labeled["submitted_at"])
    return labeled

def assert_no_future(history: pd.DataFrame, boundary: pd.Timestamp) -> None:
    if len(history) and history["submitted_dt"].max() >= boundary:
        raise LeakageError("history contains claims submitted on/after the scoring boundary")

def onboarding_check(claims: pd.DataFrame, partners: pd.DataFrame) -> dict:
    """Count claims whose partner onboarding date is after the claim, or missing/invalid.

    The scorer derives partner age as (claim time - onboarding date), so a date after the claim
    would leak information from the future into the 'new partner' signal.
    """
    ob = pd.to_datetime(partners.set_index("partner_id")["onboarded_date"], errors="coerce")
    claim_ob = claims["partner_id"].map(ob)
    return {"claims_checked": int(len(claims)),
            "onboarded_after_claim": int((claim_ob > claims["submitted_dt"]).sum()),
            "missing_or_invalid_onboarding_date": int(claim_ob.isna().sum())}

def smoothed_map(df: pd.DataFrame, col: str, global_rate: float, m: int = SMOOTHING) -> dict[str, float]:
    stats = df.groupby(col).is_fraud.agg(["sum", "count"])
    return {str(k): float((v["sum"] + m * global_rate) / (v["count"] + m)) for k, v in stats.iterrows()}

def fit_config(labeled: pd.DataFrame, partners: pd.DataFrame, as_of: pd.Timestamp | None = None) -> dict:
    """Partner statistics from `labeled`; with `as_of`, only claims strictly before it are used."""
    hist = labeled if as_of is None else labeled[labeled["submitted_dt"] < as_of]
    if as_of is not None:
        assert_no_future(hist, as_of)
    if hist.empty:
        raise ValueError("no labeled history available before the requested boundary")
    g = float(hist.is_fraud.mean())
    recent = hist[hist["submitted_dt"] >= hist["submitted_dt"].max() - pd.Timedelta(days=RECENT_DAYS)]
    rg = float(recent.is_fraud.mean())
    return {
        "version": "1.0",
        "author": "Dewansh Dewangan",
        "username": "Anszhu",
        "global_fraud_rate": g,
        "recent_global_fraud_rate": rg,
        "partner_rate": smoothed_map(hist, "partner_id", g),
        "recent_partner_rate": smoothed_map(recent, "partner_id", rg),
        "partner_onboarded_date": {str(r.partner_id): str(r.onboarded_date) for r in partners.itertuples()},
        "formula": FORMULA,
    }

def make_config(data_dir=DATA, cfg_path=CFG) -> dict:
    require(["train.csv", "partners.csv"], data_dir)
    labeled = prepare_labeled(pd.read_csv(data_dir / "train.csv"))
    config = fit_config(labeled, pd.read_csv(data_dir / "partners.csv"))
    cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config

if __name__ == "__main__":
    try:
        make_config()
    except FileNotFoundError as e:
        raise SystemExit(f"ERROR: {e}")
    print("Wrote src/model_config.json")
