# Kestrel Home — Task 2 Submission Form

Author: Dewansh Dewangan (GitHub: Anszhu)

## What did you build, and what business outcome does it move?

I built a warranty-claim review service that returns a fraud-review score and reasons for a single claim, with a Streamlit screen and a FastAPI `/score` endpoint.

The labeled history has 1.265% fraud (141 of 11,146 decided claims). A time-based Apr-Jun 2026 backtest reached 97.89% accuracy, which equals calling every claim genuine, so I did not treat it as proof of a useful fraud model. The operational objective is to prioritise the 40 claims/month the investigation desk can actually review.

In the same backtest, the top 40 claims per month contained 18 fraud cases across 120 reviewed claims and Rs 39,473 of gross fraud value: Rs 328.94 gross value of fraudulent claims surfaced per review in the validation queue (reviewing at random would give about Rs 48.85; this is not savings or ROI). Economic caveat: 102 of the 120 reviewed claims were genuine; at the policy goodwill of Rs 380 each (Rs 38,760, assuming each is held) the illustrative residual is approximately Rs 713 across the historical validation queue (about Rs 5.94 per review), before investigator time and other operational costs. That is not guaranteed savings, not a proven ROI, and not evidence of profitability. The service prioritises claims for investigation; it does not prevent fraud by itself.

## What score do you expect predictions.csv to get on the hidden outcomes, on which metric, and why that metric?

The hidden-set score has not been measured: hidden outcomes are unavailable to me. The assignment asks for an expectation, so this is an estimate only. Estimated ROC-AUC: approximately 0.80, based on the chronological Apr-Jun 2026 backtest (ROC-AUC 0.8338; bootstrap 95% interval approximately 0.745-0.908), set a little below the backtest value because partner-history behaviour was less consistent after May 2026 and the validation sample is small. The strongest evidence is the chronological Apr-Jun 2026 backtest: ROC-AUC 0.8338, average precision 0.1521, accuracy 97.8883% (equal to the all-genuine baseline), and 18 fraud in the 120 top-40-per-month reviews. The metric I would judge the file on is ROC-AUC, because the file is a ranking score and the investigation desk acts on the ranking; accuracy cannot separate a useful ranking from none when fraud is 1.265% of claims. The score never reaches 0.5, so any metric that needs a 0.5 cut-off will only reflect the fraud rate.

## How do you know it works?

I used a chronological holdout rather than a random split: for each month of Apr-Jun 2026, partner statistics were fitted only on earlier labeled claims (enforced in code and tests). Sample: 2,131 claims, 45 fraud. Results: ROC-AUC 0.8338 (bootstrap 95% interval 0.745-0.908; April 0.644, May 0.911, June 0.881), average precision 0.1521. Error rate: at a 0.5 threshold the score flags nothing, so accuracy (97.8883%) equals the all-genuine baseline and every fraud case is missed; in the top-40 queue 102 of 120 reviewed claims (85%) were genuine and could be held. The type of case it gets wrong: fraud from partners with little history (they receive portfolio baseline rates) and fraud in months where partner behaviour shifted (April ranks worst). With only 45 fraud cases these estimates are noisy. Every number comes from `python -m src.validate` and `validation/metrics.json`.

## Did you change, narrow, or push back on the client's ask?

Yes. I kept accuracy as a reported number because it was requested, but pushed back on treating >97% accuracy as evidence of useful fraud detection: with 1.265% fraud, an all-genuine model scores 97.89%. The service therefore ranks claims for the 40-a-month investigation desk, and I changed the headline measure to gross fraud value per review, with the goodwill caveat.

## What is wrong with what you are handing us, or with the data?

Hidden outcomes are unavailable, so only the Apr-Jun backtest supports the results. The score ignores claim amount: I tested two claim-amount variants and did not adopt them (a small-claim-after-1-May indicator changed ROC-AUC by -0.003 to +0.002; a small-claim indicator at any date improved Apr-Jun but badly hurt the Oct 2025-Mar 2026 window, because small claims were not riskier before the 1 May rule; see `validation/experiment_report.md`). Partner history carries the most weight. It was useful in the earlier development period (removing it cut ROC-AUC from 0.851 to 0.777) but became less consistent after May 2026 (Apr-Jun ROC-AUC essentially unchanged without it); the post-May sample is small, so the model was not retuned, and partner-history behaviour should be monitored as more outcomes arrive.

Data issues: 12,029 training rows contain 681 re-submitted claim numbers (first copy kept; their labels never conflict) and 215 blank outcomes (202 after de-duplication; excluded, not treated as genuine). All 215 blanks are in the CRM source; legacy Zoho rows contain no blanks, so open legacy cases were exported as 0 and some "genuine" legacy labels may really be undecided. 5 training rows (4 claims) have free-text claim descriptions that look like notes addressed to an AI or reviewer; they were treated as data and the scorer never reads free text. Serials are partner-typed and unused; `products.csv` is unused. Timestamps are IST; the UTC-stored legacy resolution events from the policy are not in the files. "No inspection recorded" can reflect the 1 May 2026 auto-approval rule for claims under Rs 2,000, so the reason text is policy-aware. The top-40 queue assumes each month is ranked with full-month visibility. Partner-level scores can burden good outlets, so a human must decide. Partner onboarding dates were checked against claim timestamps: none of the 11,146 labeled claims precedes its partner's onboarding date, and none is missing or invalid, so no future information enters the new-partner signal. Fitting partner rates on all labels and scoring the same window gives about 0.94 AUC, which is leakage, so I did not use it.

## What did you deliberately leave out, and why?

I did not use external paid model APIs. I also did not publish client-level data, raw claim text, or case-level prediction outputs. I did not automatically label claims as fraud because the investigation capacity and the Rs 380 goodwill cost of holding genuine claims make review prioritisation safer. I left claim amount, text, serials and customer identity out of the score: they add risk and complexity, and I could not validate them honestly in the time available.

## Anything you built or found that nobody asked for?

The service exposes human-readable reasons with each review-priority score and a risk level (HIGH/MEDIUM/LOW). The score is a ranking signal, not a calibrated probability. It also explicitly separates model score from a finding of fraud, checks the leakage boundary in code and tests, and warns that the Rs 328.94 per review is gross of goodwill cost, and ships the claim-amount and ablation experiments (`validation/experiment_report.md`).

## What did you use AI for?

AI assistance (Claude, through a chat interface) was used for implementation scaffolding, coding, tests, validation iteration and documentation review; I directed and reviewed the work. No paid model API is called by the product (paid AI API cost: ₹0 — no paid AI API used). Chat-assistant subscription cost, if any: [ENTER IF ANY]. Details in `AI_USAGE.md`. I discarded approaches that over-relied on the requested accuracy KPI or treated embedded claim text as instructions.

Screen recording: [PASTE THREE-MINUTE RECORDING LINK]

## Public Google Drive Link

[PASTE GOOGLE DRIVE LINK]

Note: the assignment wording asks for public links, but Kestrel's policy (s10) and the assignment itself forbid publishing client data. Put only material without client data here (for example the recording, or a ZIP without `src/model_config.json`); share the code through a private repository or ZIP with the address in the invitation.

## Monday handoff — three things to know

1. The score is a review-priority signal, not an automatic fraud finding.
2. Accuracy is weak as a standalone KPI because fraud prevalence is low; use the review-queue results and confirmed fraud value.
3. Keep all Kestrel client data private, including `src/model_config.json` (partner-level fraud rates). Rebuild with `python -m src.train`; check with `python -m src.validate` and `python -m pytest -q`. Next step: after another month of outcomes, re-check the partner-history weights (they appear to have drifted after 1 May 2026).

## Honest hours spent

[ENTER ACTUAL HOURS]

## Github Repo Link

[PRIVATE REPOSITORY URL]

The form field says "Public", but the repository must be PRIVATE (client data and `src/model_config.json` are confidential). Share access with the address in the invitation, as the assignment itself allows.

## What does one prediction cost, and what would a month cost at Kestrel's volume?

No paid API calls are required.

Model inference is local, so the marginal API cost per prediction is **₹0**. At approximately 750 warranty claims/month, paid API usage remains **₹0/month**. Compute/hosting costs depend on the chosen deployment environment and are separate from model-call cost.

## FINAL SUBMISSION CHECKLIST

- [x] predictions.csv generated with `python -m src.predict` and validated (2,252 rows, 2,252 unique claim IDs, columns `claim_id,score`, no NaN, scores in [0, 1], IDs match `test_unlabelled.csv` and `sample_submission.csv`, two runs byte-identical). It is included only in the private submission ZIP and is never committed to Git.
- [x] API verified (`/health`, `/score`, error cases)
- [x] Streamlit verified (headless run plus scripted UI test; not opened in a Windows browser by the assistant)
- [x] Validation verified (ROC-AUC 0.8338, AP 0.1521, top-40: 18/120, Rs 39,473 gross, Rs 328.94 gross per review; `validation/metrics.json`)
- [x] Memo complete (`memo.md`)
- [x] AI disclosure complete (`AI_USAGE.md`)
- [ ] Recording complete (follow `RECORDING_GUIDE.md`; paste link above)
- [ ] Repository access configured (private repo shared with the address in your invitation)
- [x] Privacy checked (no client files in the ZIP; `model_config.json` is client-derived and must stay private)
- [ ] Fill placeholders: recording link, Drive link, hours, private repo URL, AI cost
