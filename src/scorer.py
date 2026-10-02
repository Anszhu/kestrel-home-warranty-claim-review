"""Single-claim scorer: transparent weighted score + the reasons behind it.

Free-text fields (claim_description, inspector_note) are never read: any instruction-like
text in a claim is treated as data and has no effect on the score.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

CONFIG_PATH = Path(__file__).with_name("model_config.json")
SMALL_CLAIM_LIMIT_INR = 2000                      # ops policy s5
AUTO_APPROVAL_FROM = pd.Timestamp("2026-05-01")   # ops policy s5
NO_PARTNER_HISTORY_DAYS = 99999

DISCLAIMER = ("Higher scores indicate higher review priority. The score is a ranking signal for review prioritization, "
              "not a calibrated probability or a final fraud decision.")

class ClaimInputError(ValueError):
    """The submitted claim record is invalid; the message is safe to show to users."""

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "src/model_config.json is missing. Place the private data in data/ and run: python -m src.train"
        )
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

def _missing(v: Any) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and not v.strip())

def _number(record: dict, key: str) -> float | None:
    v = record.get(key)
    if _missing(v):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ClaimInputError(f"{key} must be a number") from None
    if math.isnan(x) or math.isinf(x) or x < 0:
        raise ClaimInputError(f"{key} must be a non-negative number")
    return x

def _timestamp(record: dict) -> pd.Timestamp | None:
    v = record.get("submitted_at")
    if _missing(v):
        return None
    try:
        return pd.Timestamp(v)
    except (ValueError, TypeError):
        raise ClaimInputError("submitted_at is not a valid date/time (use YYYY-MM-DD HH:MM)") from None

def _scalar_id(record: dict, key: str) -> str | int | float | None:
    v = record.get(key)
    if _missing(v):
        return None
    if isinstance(v, bool) or not isinstance(v, (str, int, float)):
        raise ClaimInputError(f"{key} must be a string or number")
    return v

def _inspection(record: dict) -> str | None:
    v = record.get("partner_inspected")
    if _missing(v):
        return None
    s = str(v).strip().upper()
    if s not in {"Y", "N"}:
        raise ClaimInputError("partner_inspected must be 'Y' or 'N'")
    return s

def _days_onboard(record: dict, onboarded: str | None, ts: pd.Timestamp | None) -> int | None:
    explicit = _number(record, "days_onboard")
    if explicit is not None:
        return int(explicit)
    if ts is not None and onboarded:
        return max(0, int((ts - pd.Timestamp(onboarded)).days))
    return None

def score_claim(record: dict, config: dict | None = None) -> dict:
    """Score one claim record (dict). Raises ClaimInputError for invalid values."""
    cfg = config or load_config()
    f = cfg["formula"]
    partner_id = str(_scalar_id(record, "partner_id") or "").strip()
    claim_id = _scalar_id(record, "claim_id")
    known = partner_id in cfg["partner_rate"]
    p = float(cfg["partner_rate"].get(partner_id, cfg["global_fraud_rate"]))
    p90 = float(cfg["recent_partner_rate"].get(partner_id, cfg["recent_global_fraud_rate"]))

    ts = _timestamp(record)
    prior_claims = _number(record, "customer_prior_claims") or 0.0
    amount = _number(record, "claim_amount_inr")
    inspected = _inspection(record)
    days = _days_onboard(record, cfg.get("partner_onboarded_date", {}).get(partner_id), ts)

    new_partner = float(days is not None and days < f["new_partner_days_threshold"])
    prior = float(np.clip(prior_claims / 3.0, 0, 1))
    uninspected = float(inspected == "N")
    score = float(np.clip(
        f["partner_rate_weight"] * p + f["recent_partner_rate_weight"] * p90
        + f["new_partner_weight"] * new_partner + f["prior_claims_weight"] * prior
        + f["uninspected_weight"] * uninspected, 0, 1))

    # Policy s5: inspection sign-off was required for every claim until 30 Apr 2026; from 1 May 2026
    # claims under Rs 2,000 are auto-approved without inspection. None = cannot be determined.
    if ts is None or amount is None:
        inspection_required = None
    else:
        inspection_required = not (ts >= AUTO_APPROVAL_FROM and amount < SMALL_CLAIM_LIMIT_INR)

    reasons: list[str] = []
    if not known:
        reasons.append("Partner has no history in the training data; portfolio baseline rates were used.")
    elif p >= cfg["global_fraud_rate"] * 1.75:
        reasons.append(f"Partner historical fraud rate is elevated ({p:.1%}).")
    elif p > cfg["global_fraud_rate"] * 1.15:
        reasons.append(f"Partner historical fraud rate is above the portfolio baseline ({p:.1%}).")
    if known and p90 >= cfg["recent_global_fraud_rate"] * 1.75:
        reasons.append(f"Recent partner fraud rate is elevated ({p90:.1%}).")
    if new_partner:
        reasons.append("Partner was onboarded less than 365 days before the claim.")
    if prior >= 1 / 3:
        reasons.append("Customer has at least one prior warranty claim.")
    if uninspected:
        if inspection_required is False:
            reasons.append("No partner inspection is recorded; for sub-Rs 2,000 claims submitted after 1 May 2026 "
                           "this can be consistent with the auto-approval policy.")
        elif inspection_required:
            reasons.append("No partner inspection is recorded although policy required it for this claim; "
                           "this can be a risk signal.")
        else:
            reasons.append("No partner inspection is recorded; whether policy required it could not be determined "
                           "(claim amount or submission date missing).")
    if not reasons:
        reasons.append("No elevated signal was found; score is close to the portfolio baseline.")

    return {
        "claim_id": claim_id,
        "score": round(score, 6),
        "risk_level": "HIGH" if score >= 0.20 else ("MEDIUM" if score >= 0.10 else "LOW"),
        "reasons": reasons[:5],
        "signals": {
            "historical_partner_rate": round(p, 6),
            "recent_partner_rate": round(p90, 6),
            "partner_known": known,
            "days_onboard": days if days is not None else NO_PARTNER_HISTORY_DAYS,
            "customer_prior_claims": int(prior_claims),
            "partner_inspected": inspected,
            "inspection_required_by_policy": inspection_required,
        },
    }
