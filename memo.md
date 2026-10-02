# Memo: Warranty claim review

**To:** Ritu Deshpande, Head of D2C Operations  **From:** Dewansh Dewangan

## Decision
Use the model as an **investigation-priority queue** for the desk's 40 claims a month. The review-priority score means "look at this claim first": higher scores indicate higher review priority. It is a ranking signal, not a calibrated probability or a finding of fraud, and must not block a claim on its own.

## Why accuracy is the wrong yardstick
Only 1.265% of decided claims are fraud (141 of 11,146). Calling every claim genuine scores 97.8883% accuracy, exactly what the model scores at a 0.5 cut-off (its scores never reach 0.5). The board's ">97%" target cannot show whether fraud is being found.

## Evidence (historical backtest, Apr-Jun 2026)
Each month was scored using only earlier claims. Hidden-test outcomes are unavailable, so hidden-test performance has not been measured.
- Ranking: ROC-AUC 0.8338, average precision 0.1521 (2,131 claims, 45 fraud). Months differed (April 0.644, May 0.911, June 0.881); bootstrap 95% interval 0.745 to 0.908.
- Top 40 per month (120 reviews): **18 fraud, Rs 39,473 gross fraud value, Rs 328.94 gross fraud value per review**, against about Rs 48.85 for random review.

## Economics
Rs 328.94 is the gross value of fraudulent claims surfaced per review, not savings, ROI or profit. 102 of the 120 reviewed claims were genuine; at Rs 380 goodwill each, if all are held, that is Rs 38,760. The illustrative residual is approximately Rs 713 across the historical validation queue (about Rs 5.94 per review), before investigator time, the Rs 260 service-contact cost and other operational costs (none included).

## What the data says
Partners onboarded in the last year have about twice the fraud rate (2.2% vs 1.1%), but most new partners are fine: 12 partners account for 96 of 141 confirmed frauds, and 7 of them are long-established. Since the 1 May 2026 rule, claims under Rs 2,000 are fraudulent 3.2% of the time (35 of 1,085) versus 0.3% for larger ones (1 of 337).

## Partner history
It was useful in the six months before the backtest (removing it cuts ROC-AUC from 0.851 to 0.777) but became less consistent after May 2026: in Apr-Jun, removing it leaves ROC-AUC essentially unchanged (0.8345 vs 0.8338). The post-May sample is small (45 fraud cases), so the model was not retuned on it. This does not show partner history is optimal or necessary; monitor it as more outcomes arrive. Claim-amount features were tested and not adopted: they did not hold across periods.

## Limitations
Few fraud labels and low prevalence make every figure noisy. Partner history is concentrated in a few outlets and can burden good ones, so a human decides. Fraud patterns drift, and "no inspection recorded" can simply reflect the policy for claims under Rs 2,000. Re-submitted claims were de-duplicated, undecided cases excluded, and some legacy "genuine" labels may be open cases. `src/model_config.json` holds partner-level fraud rates and is confidential.

## Next week
Send the desk the weekly top 10 and record every outcome, including genuine ones; track how many reviewed genuine claims are actually held and the goodwill paid; ask Tanmay which old Zoho "0" outcomes are really open cases; re-run `python -m src.validate` after next month's outcomes.
