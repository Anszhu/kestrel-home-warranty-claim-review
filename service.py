"""FastAPI service.  Start:  uvicorn service:app --reload --port 8000

POST /score  one claim as JSON -> score, risk level, reasons, signals
GET  /health liveness + whether the model configuration is available
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

from src.scorer import DISCLAIMER, ClaimInputError, load_config, score_claim

log = logging.getLogger("kestrel.service")
app = FastAPI(title="Kestrel Warranty Claim Review", version="1.0")

@app.get("/health")
def health() -> dict:
    try:
        load_config()
        loaded = True
    except Exception:
        loaded = False
    return {"status": "ok" if loaded else "degraded", "service": "kestrel-warranty-review",
            "model_config_loaded": loaded}

@app.post("/score")
def score(record: dict) -> dict:
    """`partner_id` is required; `claim_id` is optional (echoed back); extra fields are ignored."""
    if not str(record.get("partner_id") or "").strip():
        raise HTTPException(status_code=422, detail="partner_id is required")
    try:
        result = score_claim(record)
    except ClaimInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model configuration is not available on the server.")
    except Exception:
        log.exception("unexpected scoring failure")
        raise HTTPException(status_code=500, detail="Internal error while scoring the claim.")
    result["disclaimer"] = DISCLAIMER
    return result
