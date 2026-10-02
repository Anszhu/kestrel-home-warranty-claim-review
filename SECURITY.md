# Security and confidentiality

Author: Dewansh Dewangan (GitHub: Anszhu)

Kestrel Home data is confidential. Ops policy v4.1 s10: customer and operational data may be shared with approved vendors
for analysis, but must not be published, uploaded to public repositories, or shared beyond the engagement team.

## Rules
1. **Private repository only.** Never make this repository or ZIP public. Share access only with the people named in the assignment invitation.
2. **No raw data in Git or in the ZIP.** `train.csv`, `test_unlabelled.csv`, `partners.csv`, `products.csv`, `sample_submission.csv`, `ops-policy.pdf`, the email thread and the data-pack README stay in the git-ignored `data/` folder only.
3. **No public deployment with client data.** A hosted Streamlit app must be private/restricted. Do not deploy anything that exposes `data/`, `outputs/` or `src/model_config.json` to the public.
4. **Secrets.** No API key is required. `.env` (only holds `API_BASE_URL`) is git-ignored; `.env.example` is the safe template. Never commit credentials.
5. **Generated outputs are claim-level and private.** `outputs/predictions.csv` and `outputs/review_queue.csv` are git-ignored and never committed; regenerate with `python -m src.predict`. The private submission ZIP contains `predictions.csv` (required deliverable) and must not be uploaded publicly. Share the predictions file only through the channel the client specifies.
6. **Safe errors.** The API and UI return short messages (HTTP 422/503/500) without stack traces or server paths. Free-text claim fields are never read or executed.
7. **Approved sharing principle.** Share only with the engagement team and approved reviewers; when unsure, do not share.

## `src/model_config.json` - what it contains and why it is sensitive
Contents (no claim rows, no customer data, no free text, no serials):
- the portfolio fraud rate and the recent (90-day) portfolio rate, derived from investigation outcomes;
- a smoothed historical fraud rate for each of ~366 service partners, and a recent rate for ~365 of them;
- the onboarding date of each of ~380 partners (from `partners.csv`);
- the scoring weights.

**This artifact is confidential and the repository/package must remain private. Do not expose it in a public deployment.** Why the app needs it: single-claim scoring looks up the partner's rates and age. Why it is not public: the partner-level fraud rates are confidential results of Kestrel's investigations and name individual outlets as higher or lower risk; publishing them could defame partners, tip off bad actors, or let people tune claims to stay under the score.
Handling: keep it in the private repository/ZIP only; treat it like client data. Unused product metadata was removed from it (data minimisation).
Alternatives considered: hashing partner IDs or encrypting the file would add key management without real protection for a small private package, so a documented confidential artifact in a private repo is used. If sharing beyond the engagement team is ever needed, regenerate it from the private data on the recipient's side with `python -m src.train` instead of sending it.
