# Development experiments (same walk-forward protocol as `python -m src.validate`)

Reproduce with `python -m src.experiments` (private data required). Historical results only; no hidden-test claim.
The development window (Oct 2025 - Mar 2026) is used only to check whether a finding in the validation window (Apr - Jun 2026) is stable. B weights are fixed, documented values, not fitted on outcomes.

## Window: development_Oct2025_Mar2026 (4,409 claims, 50 fraud)

### Claim-amount experiment (A vs B)
| Variant | ROC-AUC | Avg precision | Accuracy @0.5 | Monthly ROC-AUC | Top-40 fraud | Fraud value | Gross value per review |
|---|---|---|---|---|---|---|---|
| A: current production model | 0.8505 | 0.2604 | 98.8660% | 0.8059 / 0.7806 / 0.9408 / 0.8263 / 0.9926 / 0.8111 | 32/240 | Rs 236,252 | Rs 984.38 |
| B: A + small-claim-after-1-May indicator, +0.02 | 0.8505 | 0.2604 | 98.8660% | 0.8059 / 0.7806 / 0.9408 / 0.8263 / 0.9926 / 0.8111 | 32/240 | Rs 236,252 | Rs 984.38 |
| B: A + small-claim-after-1-May indicator, +0.05 | 0.8505 | 0.2604 | 98.8660% | 0.8059 / 0.7806 / 0.9408 / 0.8263 / 0.9926 / 0.8111 | 32/240 | Rs 236,252 | Rs 984.38 |
| B: A + small-claim-after-1-May indicator, +0.1 | 0.8505 | 0.2604 | 98.8660% | 0.8059 / 0.7806 / 0.9408 / 0.8263 / 0.9926 / 0.8111 | 32/240 | Rs 236,252 | Rs 984.38 |
| B': A + small-claim indicator (any date), +0.02 | 0.8062 | 0.2146 | 98.8660% | 0.8153 / 0.6732 / 0.9309 / 0.7706 / 0.9904 / 0.7234 | 33/240 | Rs 237,006 | Rs 987.52 |
| B': A + small-claim indicator (any date), +0.05 | 0.7881 | 0.1739 | 98.8660% | 0.8215 / 0.6284 / 0.8875 / 0.7703 / 0.9840 / 0.7194 | 32/240 | Rs 220,779 | Rs 919.91 |
| B': A + small-claim indicator (any date), +0.1 | 0.7651 | 0.1250 | 98.8660% | 0.8212 / 0.6301 / 0.8321 / 0.7649 / 0.9335 / 0.6857 | 27/240 | Rs 186,057 | Rs 775.24 |

Paired bootstrap ROC-AUC difference vs A (95% interval):
- B +0.02: +0.0000 (+0.0000 to +0.0000)
- B +0.05: +0.0000 (+0.0000 to +0.0000)
- B +0.1: +0.0000 (+0.0000 to +0.0000)
- B' +0.02: -0.0446 (-0.0828 to -0.0121)
- B' +0.05: -0.0623 (-0.1144 to -0.0191)
- B' +0.1: -0.0851 (-0.1398 to -0.0359)

Small claims (< Rs 2,000) by period: {"post_1_May_2026=False": {"claims": 2711, "fraud": 11}}

### Ablation: one signal removed (weight 0)
| Variant | ROC-AUC | Avg precision | Accuracy @0.5 | Monthly ROC-AUC | Top-40 fraud | Fraud value | Gross value per review |
|---|---|---|---|---|---|---|---|
| remove_partner_history | 0.7765 | 0.0492 | 98.8660% | 0.7652 / 0.7688 / 0.8248 / 0.6943 / 0.8994 / 0.7763 | 16/240 | Rs 94,374 | Rs 393.23 |
| remove_recent_partner_rate | 0.8503 | 0.2611 | 98.8660% | 0.7955 / 0.7810 / 0.9435 / 0.8226 / 0.9914 / 0.8098 | 32/240 | Rs 236,252 | Rs 984.38 |
| remove_partner_recency | 0.8712 | 0.2695 | 98.8660% | 0.8218 / 0.8328 / 0.9631 / 0.8417 / 0.9926 / 0.8216 | 34/240 | Rs 238,031 | Rs 991.80 |
| remove_customer_prior_claims | 0.8409 | 0.2117 | 98.8660% | 0.8111 / 0.7300 / 0.8911 / 0.8621 / 0.9894 / 0.8336 | 32/240 | Rs 236,252 | Rs 984.38 |
| remove_inspection_signal | 0.8380 | 0.2554 | 98.8660% | 0.8115 / 0.7683 / 0.9458 / 0.8347 / 0.9923 / 0.7400 | 32/240 | Rs 236,252 | Rs 984.38 |

### Partner-weight sensitivity (historical weight, recent weight)
| Variant | ROC-AUC | Avg precision | Accuracy @0.5 | Monthly ROC-AUC | Top-40 fraud | Fraud value | Gross value per review |
|---|---|---|---|---|---|---|---|
| hist=0.75,recent=0.15 | 0.8505 | 0.2604 | 98.8660% | 0.8059 / 0.7806 / 0.9408 / 0.8263 / 0.9926 / 0.8111 | 32/240 | Rs 236,252 | Rs 984.38 |
| hist=0.5,recent=0.15 | 0.8500 | 0.2931 | 98.8660% | 0.7970 / 0.7859 / 0.9397 / 0.8249 / 0.9938 / 0.8150 | 32/240 | Rs 236,252 | Rs 984.38 |
| hist=0.25,recent=0.15 | 0.8465 | 0.3482 | 98.8660% | 0.7987 / 0.7959 / 0.9209 / 0.8214 / 0.9929 / 0.8169 | 31/240 | Rs 220,025 | Rs 916.77 |
| hist=0.0,recent=0.15 | 0.7765 | 0.0492 | 98.8660% | 0.7652 / 0.7688 / 0.8248 / 0.6943 / 0.8994 / 0.7763 | 16/240 | Rs 94,374 | Rs 393.23 |
| hist=0.25,recent=0.5 | 0.8480 | 0.3323 | 98.8660% | 0.8064 / 0.7921 / 0.9237 / 0.8290 / 0.9929 / 0.8214 | 32/240 | Rs 236,252 | Rs 984.38 |

### Signal contributions in the current score
| Signal | Mean (score points) | Std | Share of score spread |
|---|---|---|---|
| remove_partner_history | 0.0083 | 0.0251 | 47.5% |
| remove_recent_partner_rate | 0.0017 | 0.0033 | 6.3% |
| remove_partner_recency | 0.0039 | 0.0118 | 22.4% |
| remove_customer_prior_claims | 0.0041 | 0.0074 | 14.0% |
| remove_inspection_signal | 0.0014 | 0.0051 | 9.7% |

## Window: validation_Apr_Jun2026 (2,131 claims, 45 fraud)

### Claim-amount experiment (A vs B)
| Variant | ROC-AUC | Avg precision | Accuracy @0.5 | Monthly ROC-AUC | Top-40 fraud | Fraud value | Gross value per review |
|---|---|---|---|---|---|---|---|
| A: current production model | 0.8338 | 0.1521 | 97.8883% | 0.6443 / 0.9109 / 0.8806 | 18/120 | Rs 39,473 | Rs 328.94 |
| B: A + small-claim-after-1-May indicator, +0.02 | 0.8313 | 0.1539 | 97.8883% | 0.6443 / 0.9152 / 0.8826 | 18/120 | Rs 39,473 | Rs 328.94 |
| B: A + small-claim-after-1-May indicator, +0.05 | 0.8337 | 0.1586 | 97.8883% | 0.6443 / 0.9152 / 0.8853 | 18/120 | Rs 39,473 | Rs 328.94 |
| B: A + small-claim-after-1-May indicator, +0.1 | 0.8356 | 0.1731 | 97.8883% | 0.6443 / 0.9153 / 0.8882 | 19/120 | Rs 40,250 | Rs 335.42 |
| B': A + small-claim indicator (any date), +0.02 | 0.8389 | 0.1561 | 97.8883% | 0.6510 / 0.9152 / 0.8826 | 18/120 | Rs 39,473 | Rs 328.94 |
| B': A + small-claim indicator (any date), +0.05 | 0.8438 | 0.1578 | 97.8883% | 0.6706 / 0.9152 / 0.8853 | 18/120 | Rs 39,473 | Rs 328.94 |
| B': A + small-claim indicator (any date), +0.1 | 0.8464 | 0.1704 | 97.8883% | 0.6751 / 0.9153 / 0.8882 | 19/120 | Rs 40,250 | Rs 335.42 |

Paired bootstrap ROC-AUC difference vs A (95% interval):
- B +0.02: -0.0025 (-0.0168 to +0.0055)
- B +0.05: -0.0001 (-0.0150 to +0.0099)
- B +0.1: +0.0017 (-0.0132 to +0.0120)
- B' +0.02: +0.0051 (-0.0023 to +0.0139)
- B' +0.05: +0.0100 (+0.0002 to +0.0222)
- B' +0.1: +0.0126 (+0.0020 to +0.0258)

Small claims (< Rs 2,000) by period: {"post_1_May_2026=False": {"claims": 446, "fraud": 5}, "post_1_May_2026=True": {"claims": 1085, "fraud": 35}}

### Ablation: one signal removed (weight 0)
| Variant | ROC-AUC | Avg precision | Accuracy @0.5 | Monthly ROC-AUC | Top-40 fraud | Fraud value | Gross value per review |
|---|---|---|---|---|---|---|---|
| remove_partner_history | 0.8345 | 0.3760 | 97.8883% | 0.5930 / 0.9268 / 0.9138 | 21/120 | Rs 42,887 | Rs 357.39 |
| remove_recent_partner_rate | 0.8336 | 0.1536 | 97.8883% | 0.6418 / 0.9162 / 0.8818 | 17/120 | Rs 37,276 | Rs 310.63 |
| remove_partner_recency | 0.7372 | 0.1009 | 97.8883% | 0.6679 / 0.5270 / 0.8569 | 15/120 | Rs 34,164 | Rs 284.70 |
| remove_customer_prior_claims | 0.8440 | 0.1582 | 97.8883% | 0.7002 / 0.9071 / 0.8841 | 14/120 | Rs 32,822 | Rs 273.52 |
| remove_inspection_signal | 0.8411 | 0.1375 | 97.8883% | 0.6636 / 0.8774 / 0.8763 | 17/120 | Rs 38,047 | Rs 317.06 |

### Partner-weight sensitivity (historical weight, recent weight)
| Variant | ROC-AUC | Avg precision | Accuracy @0.5 | Monthly ROC-AUC | Top-40 fraud | Fraud value | Gross value per review |
|---|---|---|---|---|---|---|---|
| hist=0.75,recent=0.15 | 0.8338 | 0.1521 | 97.8883% | 0.6443 / 0.9109 / 0.8806 | 18/120 | Rs 39,473 | Rs 328.94 |
| hist=0.5,recent=0.15 | 0.8365 | 0.1609 | 97.8883% | 0.6433 / 0.9140 / 0.8839 | 19/120 | Rs 40,250 | Rs 335.42 |
| hist=0.25,recent=0.15 | 0.8358 | 0.2320 | 97.8883% | 0.6394 / 0.9180 / 0.8978 | 20/120 | Rs 42,245 | Rs 352.04 |
| hist=0.0,recent=0.15 | 0.8345 | 0.3760 | 97.8883% | 0.5930 / 0.9268 / 0.9138 | 21/120 | Rs 42,887 | Rs 357.39 |
| hist=0.25,recent=0.5 | 0.8418 | 0.2123 | 97.8883% | 0.6425 / 0.9026 / 0.8976 | 20/120 | Rs 42,245 | Rs 352.04 |

### Signal contributions in the current score
| Signal | Mean (score points) | Std | Share of score spread |
|---|---|---|---|
| remove_partner_history | 0.0093 | 0.0284 | 45.0% |
| remove_recent_partner_rate | 0.0019 | 0.0036 | 5.6% |
| remove_partner_recency | 0.0055 | 0.0138 | 21.8% |
| remove_customer_prior_claims | 0.0044 | 0.0075 | 11.8% |
| remove_inspection_signal | 0.0109 | 0.0100 | 15.8% |

## How to read the partner-history results

Partner history was useful in the earlier development period (removing it cut ROC-AUC from 0.851 to 0.777 and top-40 hits from 32 to 16 of 240) but became less consistent after May 2026: in Apr-Jun 2026 removing it left ROC-AUC essentially unchanged (0.8338 to 0.8345) and raised average precision (0.1521 to 0.3760) and top-40 hits (18 to 21), although April ranked worse without it (0.644 to 0.593) while May and June ranked better. The post-May validation sample is still small (45 fraud cases across Apr-Jun), so the existing model was not retuned solely on that period. Partner-history behaviour should be monitored as more post-May outcomes become available. These results do not show that partner history is optimal, nor that it is definitely necessary.
