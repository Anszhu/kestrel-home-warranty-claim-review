# Kestrel Home - Warranty Claim Review (Variant C)

**Author:** Dewansh Dewangan  **GitHub:** Anszhu

> **THIS REPOSITORY / PACKAGE MUST REMAIN PRIVATE.** Kestrel client data is confidential and `src/model_config.json`
> contains client-derived partner statistics. Never publish them or put this project in a public repository or deployment.

## 1. What it does
A **review-priority / investigation-ranking model** for warranty claims. Kestrel's investigation desk can review at most
40 claims a month, so the model ranks claims for human review; it does **not** find or declare fraud. Pieces: scoring
library (`src/`), FastAPI service (`service.py`), Streamlit screen (`app.py`). No paid API or key is required.

## 2. Folder structure
```
app.py  service.py  requirements.txt  .env.example  README.md  SECURITY.md  AI_USAGE.md  memo.md  submission-form.md  RECORDING_GUIDE.md
src/       paths.py train.py predict.py validate.py experiments.py scorer.py model_config.json (confidential)
tests/     test_scorer.py test_service.py test_pipeline.py test_privacy.py test_metrics_docs.py test_app.py (synthetic data only)
data/      PRIVATE inputs (git-ignored)        outputs/  generated private outputs (git-ignored)      models/  reserved
validation/ metrics.json (single source of truth), validation_report.md, experiments.json, experiment_report.md
scripts/   setup.bat run_api.bat run_streamlit.bat run_local.bat
```

## 3. Requirements
Python 3.10, 3.11 or 3.12 (tested on 3.12). Packages: `requirements.txt` (fastapi, uvicorn, streamlit, pandas, requests, scikit-learn; pytest and httpx for tests). `.env` is read by a small built-in loader, so python-dotenv is not needed.

## 4. Setup
Windows: run `scripts\setup.bat`, or manually:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
macOS/Linux: `source .venv/bin/activate`. Optionally copy `.env.example` to `.env` to change `API_BASE_URL` (default `http://127.0.0.1:8000`).

## 5. Private data
Put these in `data/` (see `data/README.md`): `train.csv`, `test_unlabelled.csv`, `partners.csv`, `products.csv` (and `sample_submission.csv`, used to check the output shape). `products.csv` is part of the data pack but is not used by the current score. Without the files, the API and app still start and score single claims, and every command explains what is missing.

## 6. Train, predict, validate
```
python -m src.train        # rebuild src/model_config.json   (train.csv, partners.csv)
python -m src.predict      # outputs/predictions.csv = claim_id,score  + outputs/review_queue.csv   (test_unlabelled.csv)
python -m src.validate     # chronological validation -> validation/metrics.json, validation_report.md
python -m src.experiments  # claim-amount and ablation experiments -> validation/experiment_report.md
```
`predictions.csv` has exactly the columns `claim_id,score`, one row per test claim, scores in [0, 1], deterministic for the same config and data. It and the review queue are claim-level and git-ignored. The private submission ZIP (not the repository) carries a copy of `predictions.csv` at its top level; never publish it.

## 7. Run the API
```
uvicorn service:app --reload --port 8000
```
`GET /health` and `POST /score` (docs at http://127.0.0.1:8000/docs).

## 8. Run Streamlit
```
streamlit run app.py
```
Five tabs: overview and data status, score a claim, API test (needs the API running), review queue, model and validation. `scripts\run_local.bat` starts both.

## 9. Test
```
python -m pytest -q
```
Tests use only synthetic data (labelled as such) and check scoring, API errors, the pipeline, the leakage boundary, privacy, and that the documentation agrees with `validation/metrics.json`.

## 10. API example (made-up values)
```
curl -X POST http://127.0.0.1:8000/score -H "Content-Type: application/json" \
  -d '{"claim_id":"EXAMPLE-001","partner_id":"SP3207","partner_inspected":"N","customer_prior_claims":1}'
```
Response: `{"claim_id","score","risk_level","reasons","signals","disclaimer"}`. `score` is the review-priority score: higher means review sooner. It is a ranking signal for review prioritization, not a calibrated probability or a final fraud decision. `risk_level` is HIGH (score >= 0.20), MEDIUM (>= 0.10) or LOW. `partner_id` is required, `claim_id` optional, extra fields are ignored. Invalid values, wrong types or malformed JSON return **422**; a missing model config returns **503**; any unexpected error returns a generic **500**. Errors never include stack traces or server paths. Free-text fields (claim description, inspector note) are never read: instruction-like text in a claim is data.

## 11. Model
A transparent weighted review-priority score (a ranking signal, not a calibrated probability): smoothed historical partner fraud rate (0.75), recent 90-day partner rate (0.15), partner onboarded < 365 days before the claim (0.04), customer prior claims (0.04), no partner inspection recorded (0.02). Reasons returned correspond to these signals. Inspection is policy-aware: all claims needed sign-off until 30 Apr 2026, and from 1 May 2026 claims under Rs 2,000 are auto-approved without it, so the reason text says "can be consistent with the auto-approval policy" in that case and "can be a risk signal" when inspection was required.
Data handling: blank outcomes (undecided) are excluded, never treated as genuine or fraud; duplicate claim IDs (partner re-submissions) are de-duplicated keeping the first copy (labels never conflict); serials, free text and `products.csv` are not used.

## 12. Validation (historical Apr-Jun 2026 backtest)
Hidden-test outcomes are unavailable, so hidden-test performance has not been measured. Walk-forward by month; each month uses partner statistics fitted only on earlier claims (`fit_config(as_of=...)`, `assert_no_future`, tests with poisoned future rows). All numbers below come from `python -m src.validate` / `validation/metrics.json`.

| Metric | Value |
|---|---|
| Labeled rows / fraud | 11,146 / 141 (1.265%) |
| Validation claims / fraud | 2,131 / 45 |
| ROC-AUC | 0.8338 (bootstrap 95% interval 0.745-0.908; 2,000 resamples, seed 42) |
| Monthly ROC-AUC Apr / May / Jun | 0.6443 / 0.9109 / 0.8806 |
| Average precision | 0.1521 |
| Accuracy at 0.5 | 97.8883% (the all-genuine baseline; the score never reaches 0.5) |
| Top-40 per month | 18 fraud / 120 reviewed |
| Gross fraud value in queue | Rs 39,473 |
| Gross fraud value per review | Rs 328.94 (random review about Rs 48.85) |
| Partner onboarding-date check | 0 of 11,146 labeled claims precede their partner's onboarding date; 0 missing or invalid |

## 13. Business interpretation
Rs 328.94 is the **gross value of fraudulent claims surfaced per review** in the validation queue (claim amount of confirmed fraud). It is not savings, net benefit, ROI, profit or realised value. Assumptions: 40 reviews a month; Rs 380 goodwill per genuine reviewed claim (assuming each is held); investigator time and the Rs 260 service-contact cost are not included. 102 of the 120 reviewed claims were genuine; at Rs 380 goodwill each (Rs 38,760, assuming each is held) the illustrative residual is approximately **Rs 713** across the historical validation queue (about Rs 5.94 per review), before investigator time and other operational costs. This is not guaranteed savings, not a proven ROI and not evidence the model is profitable.
Experiments (`validation/experiment_report.md`): two claim-amount variants were tested and **not adopted** (no stable gain across windows). Partner history was useful in the earlier development period (Oct 2025-Mar 2026) but became less consistent after May 2026; the post-May sample is small (45 fraud cases across Apr-Jun), so the model was not retuned on it. This does not show partner history is optimal or definitely necessary; monitor it as more post-May outcomes become available.

## 14. Human-labelled sample and payment reconciliation
The author confirms that a relevant sample was personally checked and is genuinely human-labelled. No separate sample file was supplied with this handoff, so its size, labelling method, comparison with model outputs, and any metrics cannot be independently reproduced here. This is a qualitative confirmation only; it is separate from the investigation outcomes used to train and backtest the model, and it does not establish model accuracy.

The Kestrel files contain claim and investigation data, but no payment ledger or payout events. They therefore cannot establish whether a claim was paid twice or support a rupee reconciliation to zero. Duplicate `claim_id` rows are partner re-submissions and are de-duplicated by keeping the first row; that data-cleaning rule is not a double-payout check.

## 15. Limitations
Only 45 fraud cases in validation, so every metric is noisy; month-to-month ranking quality varies; accuracy at 0.5 is uninformative; claim amount is not in the score; "no inspection recorded" can reflect policy; some legacy "genuine" labels may be open cases; partner history can burden good outlets, so use only as a prompt for human review.

## 16. AI disclosure
See `AI_USAGE.md`: AI assistance (Claude) was used for coding/scaffolding, tests, validation iteration and documentation review; no paid API is used by the product.

## 17. Privacy and deployment
See `SECURITY.md`. Kestrel's policy (s10) forbids publishing the data or sharing it beyond the engagement team. `.gitignore` excludes data, outputs, CSVs, PDFs and secrets. `src/model_config.json` is confidential (partner-level fraud rates, recent rates, onboarding dates, scoring weights; no claim rows or free text): keep the repository and ZIP private and never expose them in a public deployment. A Streamlit deployment (entry point `app.py`) must be private/restricted.

