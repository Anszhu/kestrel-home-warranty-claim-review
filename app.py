"""Kestrel Home - Warranty Claim Review (Streamlit).  Run:  streamlit run app.py
Author: Dewansh Dewangan (GitHub: Anszhu)."""
from __future__ import annotations

import json

import pandas as pd
import requests
import streamlit as st

from src.paths import DATA, METRICS, OUT, REQUIRED_FILES, api_base_url
from src.scorer import DISCLAIMER, ClaimInputError, score_claim

st.set_page_config(page_title="Kestrel Warranty Claim Review", layout="wide")
st.title("Kestrel Home - Warranty Claim Review")
st.caption("Review-priority prototype  |  Dewansh Dewangan (GitHub: Anszhu)  |  No paid API required")

tab_home, tab_score, tab_api, tab_queue, tab_model = st.tabs(
    ["Overview & data status", "Score a claim", "API test", "Review queue", "Model & validation"])

def claim_form(prefix: str) -> dict:
    """Shared claim input widgets. Free-text is sent as data and never interpreted."""
    a, b = st.columns(2)
    with a:
        rec = {
            "claim_id": st.text_input("Claim ID", "EXAMPLE-001", key=prefix + "id"),
            "partner_id": st.text_input("Partner ID", "SP3207", key=prefix + "p"),
            "submitted_at": st.text_input("Submitted at (YYYY-MM-DD HH:MM)", "2026-07-15 10:00", key=prefix + "t"),
            "claim_amount_inr": st.number_input("Claim amount (INR)", 0, 1_000_000, 1500, key=prefix + "a"),
        }
    with b:
        rec["customer_prior_claims"] = st.number_input("Customer prior claims", 0, 100, 1, key=prefix + "c")
        rec["partner_inspected"] = st.selectbox("Partner inspection sign-off", ["Y", "N"], index=1, key=prefix + "i")
        rec["claim_description"] = st.text_area("Claim description (data only; never used as instructions)",
                                                "Motor stopped working", key=prefix + "d")
    return rec

def show_result(r: dict) -> None:
    c1, c2 = st.columns(2)
    c1.metric("Review-priority score", f"{r['score']:.4f}", help="Higher score = review sooner. Not a probability.")
    c2.metric("Risk level", r["risk_level"], help="HIGH >= 0.20, MEDIUM >= 0.10, otherwise LOW (score thresholds).")
    st.markdown("**Reasons**")
    for reason in r["reasons"]:
        st.write("- " + reason)
    with st.expander("Signals used"):
        st.json(r["signals"])
    st.caption(r.get("disclaimer", DISCLAIMER))

# ---------------------------------------------------------------- overview
with tab_home:
    st.warning("This is a review-priority / investigation-ranking model. It orders claims for the investigation desk "
               "(capacity: 40 claims per month). It does NOT decide that a claim is fraudulent.")
    st.markdown("Higher score means review sooner. The score is a ranking signal for review prioritization, "
                "not a calibrated probability or a final fraud decision.")
    st.markdown(
        "**Objective:** spend the limited investigation capacity on the claims most worth a human look. "
        "Fraud is only about 1.3% of decided claims, so a '97% accurate' model can simply call everything genuine; "
        "the useful measure is fraud value found per claim reviewed.")
    st.subheader("Private data status")
    status = pd.DataFrame([{"file": f, "status": "present" if (DATA / f).exists() else "MISSING"} for f in REQUIRED_FILES])
    st.dataframe(status, hide_index=True)
    if (status.status == "MISSING").any():
        st.info("Private Kestrel input files are not present. Place the required files in the `data/` folder to enable "
                "training, validation and the review queue. Scoring a single claim still works from the bundled model "
                "configuration. Never upload these files to a public place.")
    st.code("1) uvicorn service:app --reload --port 8000\n2) streamlit run app.py     (second terminal)", language="bash")

# ---------------------------------------------------------------- score a claim
with tab_score:
    st.caption("Scores locally with the bundled model configuration (no API needed).")
    rec = claim_form("s_")
    if st.button("Score claim", type="primary"):
        try:
            with st.spinner("Scoring..."):
                result = score_claim(rec)
            show_result(result)
        except ClaimInputError as e:
            st.error(f"Invalid claim: {e}")
        except FileNotFoundError:
            st.error("Model configuration not found. Run `python -m src.train` with the private data in `data/`.")
        except Exception:
            st.error("Unexpected error while scoring this claim.")

# ---------------------------------------------------------------- API test
with tab_api:
    base = api_base_url()
    st.write(f"API base URL: `{base}`  (change with `API_BASE_URL` in `.env`)")
    down = ("API not reachable. Start it in another terminal: "
            "`uvicorn service:app --reload --port 8000`")
    if st.button("Check API health"):
        try:
            with st.spinner("Calling /health..."):
                h = requests.get(base + "/health", timeout=5)
            st.json(h.json())
        except (requests.RequestException, ValueError):
            st.error(down)
    rec = claim_form("a_")
    if st.button("Send to API", type="primary"):
        st.markdown("**Request** (POST /score)")
        st.code(json.dumps(rec, indent=2), language="json")
        try:
            with st.spinner("Calling /score..."):
                resp = requests.post(base + "/score", json=rec, timeout=10)
            st.markdown(f"**Response** (HTTP {resp.status_code})")
            body = resp.json()
            st.json(body)
            if resp.ok:
                show_result(body)
            else:
                st.error(f"The API rejected the request: {body.get('detail', 'unknown error')}")
        except (requests.RequestException, ValueError):
            st.error(down)

# ---------------------------------------------------------------- review queue
with tab_queue:
    queue_file = OUT / "review_queue.csv"
    if not queue_file.exists():
        st.info("No predictions yet. Place the private files in `data/` and run `python -m src.predict`.")
    else:
        try:
            q = pd.read_csv(queue_file)[["claim_id", "score", "risk_level", "reasons"]]
            n = st.slider("Show top N claims", 10, 100, 40)
            st.dataframe(q.head(n), hide_index=True)
            st.caption("Only claim_id, score, risk level and reasons are shown. The desk can review 40 claims a month.")
        except (KeyError, ValueError, pd.errors.ParserError):
            st.error("outputs/review_queue.csv is unreadable. Regenerate it with `python -m src.predict`.")

# ---------------------------------------------------------------- model & validation
with tab_model:
    st.subheader("Historical validation (Apr-Jun 2026 backtest)")
    st.info("Hidden-test outcomes are unavailable, so hidden-test performance has not been measured. "
            "The strongest evidence is the chronological Apr-Jun 2026 backtest below.")
    if not METRICS.exists():
        st.info("validation/metrics.json not found. Run `python -m src.validate` (needs the private data).")
    else:
        m = json.loads(METRICS.read_text(encoding="utf-8"))
        b = m["bootstrap_auc"]
        st.write(f"Chronological walk-forward validation: {m['val_rows']:,} labeled claims ({m['val_fraud']} fraud). "
                 f"Partner statistics for each month use only earlier claims. Training labels: {m['labeled_rows']:,} rows, "
                 f"{m['fraud_rows']} fraud ({m['fraud_prevalence']:.3%}).")
        a1, a2, a3 = st.columns(3)
        a1.metric("ROC-AUC", f"{m['roc_auc']:.4f}", help=f"Bootstrap 95% interval {b['ci_low']:.3f}-{b['ci_high']:.3f} "
                  f"({b['n_resamples']:,} resamples, seed {b['seed']}).")
        a2.metric("Average precision", f"{m['avg_precision']:.4f}")
        a3.metric("Accuracy @ 0.5", f"{m['accuracy_at_0.5']:.4%}",
                  help=f"All-genuine baseline: {m['all_genuine_accuracy']:.4%}. The score never reaches 0.5.")
        st.caption("Monthly ROC-AUC: " + "; ".join(
            f"{k} {x['roc_auc']:.3f} ({x['fraud']} fraud)" if x["roc_auc"] is not None else f"{k} not defined"
            for k, x in m["monthly"].items()))
        st.markdown("**Review capacity: 40 claims/month -> top-40 queue**")
        d, e, f = st.columns(3)
        d.metric("Fraud in queue", f"{m['queue_fraud']} / {m['queue_reviewed']}")
        e.metric("Gross fraud value in queue", f"Rs {m['queue_fraud_value_inr']:,.0f}")
        f.metric("Gross fraud value per review", f"Rs {m['fraud_value_per_review_inr']:,.2f}",
                 help="Gross value of fraudulent claims surfaced per review in the validation queue; not savings or ROI. "
                      f"Random review would give about Rs {m['random_review_fraud_value_per_review_inr']:,.2f}.")
        st.warning(f"Economic caveat: {m['genuine_in_queue']} of the {m['queue_reviewed']} reviewed claims were genuine. At Rs 380 "
                   f"goodwill per genuine reviewed claim that is Rs {m['goodwill_if_all_genuine_held_inr']:,.0f}. The illustrative "
                   f"residual after this goodwill-cost assumption is approximately Rs {m['residual_after_goodwill_inr']:,.0f} across the "
                   f"historical validation queue (about Rs {m['residual_per_review_inr']:.2f} per review), before investigator time, the "
                   "Rs 260 service-contact cost and other operational costs (not included). This is not guaranteed savings or a proven ROI.")
    st.markdown(
        "**Limitations**\n"
        "- Only 45 fraud cases in the validation window: every metric is noisy.\n"
        "- Accuracy at 0.5 equals the all-genuine baseline; the value is in the ranking.\n"
        "- Claim amount is not in the score (a tested claim-amount variant was not adopted; see `validation/experiment_report.md`).\n"
        "- 'No inspection recorded' can simply reflect the 1 May 2026 auto-approval policy for claims under Rs 2,000.\n"
        "- Partner history dominates the score. It was useful in the earlier development period but less consistent after May 2026 on a small sample; it was not retuned and should be monitored.\n"
        "- Some legacy-system 'genuine' labels may really be undecided cases.\n"
        "- Partner history can burden good outlets: use as a prompt for human review only.\n"
        "- `src/model_config.json` is confidential (client-derived partner statistics).")
