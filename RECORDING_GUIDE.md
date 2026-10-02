# Screen-recording guide (max 3 minutes, no slides)

Do not show raw Kestrel files, claim text or the contents of `data/`. Use only the app, API calls and validation numbers.
Before recording: start the API and Streamlit (`scripts\run_local.bat`) with the private data present so the review queue is populated; close other windows.

| Time | What to show / say |
|---|---|
| 0:00-0:20 | **Business problem.** Kestrel wants to flag warranty fraud before payout; the board KPI is >97% accuracy; fraud is only 1.265% of claims and the desk can review 40 a month. So this is a review-priority ranking, not a fraud detector. |
| 0:20-0:50 | **Streamlit overview.** Warning banner, private-data status, no paid API required. |
| 0:50-1:20 | **Score a claim.** Score the example and read the reasons and signals. Say that the score is a review-priority ranking (higher means review sooner), not a probability; show that "no inspection recorded" is explained by the 1 May 2026 policy for a small claim and is a risk signal only when inspection was required. Optionally type "ignore previous instructions" in the description: nothing changes. |
| 1:20-1:50 | **API request/response.** Check health, send the request, show the JSON (score, risk_level, reasons, signals, disclaimer). Show a bad input returning a clear 422. |
| 1:50-2:20 | **Validation and business result** (Model & validation tab). Apr-Jun 2026 backtest: ROC-AUC 0.8338, average precision 0.1521, accuracy 97.8883% = all-genuine baseline; top 40 a month found 18 fraud in 120 reviews, Rs 39,473 and Rs 328.94 gross per review. Then the goodwill caveat: illustrative residual about Rs 713 before investigator time. Say that hidden outcomes are unavailable and no hidden score is claimed. |
| 2:20-2:50 | **Tried, changed, discarded.** Accuracy-first thinking and random splits discarded for time-based validation; leakage check (scoring with all-data partner rates looks like AUC 0.94 but is invalid); claim-amount variants tested and not adopted because they did not hold across windows; ablation showed partner history matters but drifted after 1 May; free text never executed; no client data published. |
| 2:50-3:00 | **Close.** A review-priority system for human investigators; AI assistance is disclosed in `AI_USAGE.md`. |
