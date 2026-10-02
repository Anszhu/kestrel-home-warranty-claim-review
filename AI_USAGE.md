# AI usage disclosure

**Author and owner of this work:** Dewansh Dewangan (GitHub: `Anszhu`)

## What AI was used for
An AI assistant (Claude, through a chat interface) was used under my direction for:
- coding and scaffolding: the FastAPI service, the Streamlit screen, the Windows launch scripts;
- test assistance: writing and extending the test suite (scoring, API, pipeline, leakage, privacy, documentation consistency);
- validation iteration: the walk-forward script, the leakage boundary, the experiment and ablation scripts;
- documentation drafts (README, SECURITY, memo, recording guide), which I reviewed.

## What was run and checked
The assistant ran the pipeline and tests in its own environment: training, prediction, validation, experiments, pytest, the API, and Streamlit (a headless run and a scripted UI test), and repeated them from an extracted copy of the final ZIP in a new virtual environment. The `.bat` scripts were **not** executed on Windows by the assistant; they were checked statically only. I am responsible for the submission and should re-run it on my machine.

## What changed along the way (development notes)
- The first draft's metrics (ROC-AUC 0.8368, AP 0.1542, accuracy 97.8918%) could not be reproduced. The scripted rerun (0.8338, 0.1521, 97.8883%; top-40 result identical) replaced them everywhere.
- The unused product table was removed from the model file; the "no inspection" reason became policy-aware; validation now computes every quoted statistic (monthly AUC, bootstrap interval, top-40 queue); speculative hidden-test estimates were removed.
- Claim-amount variants and a one-signal-at-a-time ablation were evaluated and documented; the production model was left unchanged.
- A final review checked partner onboarding dates against claim timestamps (no violations), replaced percentage-style score display with a plain review-priority score, and tightened the economic wording.

## Discarded approaches
- treating >97% accuracy as sufficient (an all-genuine model reaches it);
- a generic classifier that ranked later months poorly;
- ranking partners without the 40-claims-per-month capacity framing;
- random train/test splits for time-ordered data, and scoring the validation window with all-data partner rates (looks like AUC ~0.94, but is leakage);
- following instruction-like text in claim descriptions (it is data, never executed);
- publishing client-level data or outputs;
- claim-amount features (not stable across time windows).

## Cost
Paid AI API cost: **₹0 — no paid AI API used.** The product calls no model API and needs no key. Chat-assistant subscription cost, if any: [ENTER IF ANY]. Hours: [ENTER ACTUAL HOURS].
