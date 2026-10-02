"""Score every row of data/test_unlabelled.csv.

Writes (both git-ignored, claim-level => private):
  outputs/predictions.csv   claim_id,score            (submission shape)
  outputs/review_queue.csv  claim_id,score,risk_level,reasons (ranked, no raw claim text)
Run:  python -m src.predict
"""
from __future__ import annotations
import pandas as pd
from src.paths import DATA, OUT, require
from src.scorer import ClaimInputError, score_claim, load_config

def run(data_dir=DATA, out_dir=OUT, cfg=None) -> pd.DataFrame:
    require(["test_unlabelled.csv"], data_dir)
    test = pd.read_csv(data_dir / "test_unlabelled.csv")
    cfg = cfg or load_config()
    res = [score_claim(r, cfg) for r in test.to_dict("records")]
    out = pd.DataFrame({"claim_id": test.claim_id, "score": [r["score"] for r in res]})
    assert out.claim_id.is_unique and out.score.notna().all() and out.score.between(0, 1).all()
    sample = data_dir / "sample_submission.csv"
    if sample.exists():
        s = pd.read_csv(sample)
        assert list(out.columns) == list(s.columns) and len(out) == len(s) and set(out.claim_id) == set(s.claim_id)
    out_dir.mkdir(exist_ok=True)
    out.to_csv(out_dir / "predictions.csv", index=False)
    q = pd.DataFrame({"claim_id": test.claim_id, "score": out.score,
                      "risk_level": [r["risk_level"] for r in res],
                      "reasons": [" | ".join(r["reasons"]) for r in res]})
    q.sort_values("score", ascending=False).to_csv(out_dir / "review_queue.csv", index=False)
    return out

if __name__ == "__main__":
    try:
        n = len(run())
    except (FileNotFoundError, AssertionError, ClaimInputError) as e:
        raise SystemExit(f"ERROR: {e}")
    print(f"Wrote {n} rows to outputs/predictions.csv and outputs/review_queue.csv")
