# Validation report (historical backtest, NOT hidden-test performance)

Hidden-test outcomes are unavailable, so hidden-test performance has not been measured. The strongest evidence is the
chronological Apr-Jun 2026 backtest below. Every number here is produced by `python -m src.validate` and stored in
`validation/metrics.json` (single source of truth).

## Protocol
Walk-forward by month. For each of Apr, May, Jun 2026 the partner statistics are fitted only on labeled claims submitted
before that month starts (`fit_config(..., as_of=...)` + `assert_no_future`; tests poison future rows to prove it).
Blank (undecided) outcomes are excluded; duplicate claim IDs are de-duplicated keeping the first copy.
Partner onboarding dates are static attributes; the check below confirms no labeled claim precedes its partner's onboarding date
(claims checked: 11,146; onboarded after the claim: 0; missing or invalid date: 0).

- Labeled rows: 11,146; fraud rows: 141 (1.265%)
- Validation rows Apr-Jun 2026: 2,131 (45 fraud)

## Ranking and accuracy
| Metric | Value |
|---|---|
| ROC-AUC | 0.8338 |
| Average precision | 0.1521 |
| Accuracy at 0.5 | 97.8883% (all-genuine baseline: 97.8883%; the score never reaches 0.5) |
| Bootstrap 95% interval for ROC-AUC | 0.745 - 0.908 (2,000 resamples of validation claims, seed 42) |

| Month | Claims | Fraud | ROC-AUC |
|---|---|---|---|
| 2026-04 | 709 | 9 | 0.6443 |
| 2026-05 | 709 | 14 | 0.9109 |
| 2026-06 | 713 | 22 | 0.8806 |

## Top-40-per-month review queue
- Fraud found: **18 fraud / 120 reviewed**
- Gross fraud value in the queue: **Rs 39,473**; per review: **Rs 328.94**. This is the gross value of fraudulent claims surfaced per review in the validation queue (claim amounts of confirmed fraud); it is not savings, net benefit, ROI, profit or realised value. Reviewing at random would surface about Rs 48.85 per review.
- Economic caveat: 102 of the 120 reviewed claims were genuine. At Rs 380 goodwill per genuine reviewed claim (policy s4, assuming each is held) that is Rs 38,760. Illustrative residual after this goodwill assumption is approximately **Rs 713** across the historical validation queue (about Rs 5.94 per review), before investigator time, the Rs 260 service-contact cost and other operational costs (none of which are included). This is not guaranteed savings, not a proven ROI, and not evidence that the model is profitable.
- The queue is the top 40 claims per calendar month ranked with full-month visibility; an operational queue would be built as claims arrive.

## Limitations
Scores are review-priority rankings, not calibrated probabilities. Only 45 fraud cases in the validation window, so all figures are noisy and month-to-month ranking quality varies; accuracy at 0.5 equals the all-genuine baseline; claim amount is not in the score; some legacy "genuine" labels may really be undecided cases.
