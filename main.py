"""
main.py
-------
FastAPI backend for the Personalized Networking Assistant.

Endpoints (matching the architecture diagram's API layer):
    POST /api/v1/generate   -> extract themes + generate conversation starters
    GET  /api/v1/verify     -> fact-check a query via Wikipedia
    POST /api/v1/feedback   -> record thumbs up/down on a generated interaction
    GET  /api/v1/history    -> list past interactions

Run with:
    uvicorn backend.main:app --reload
"""

import json
import logging

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import init_db, get_db, InteractionLog
from backend.models.schemas import (
    GenerateRequest, GenerateResponse,
    VerifyRequest, VerifyResponse,
    FeedbackRequest,
    HistoryResponse, HistoryItem,
)
from backend.services import nlp_service, factcheck_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("networking-assistant")

app = FastAPI(
    title="Personalized Networking Assistant API",
    description="Generates tailored conversation starters and fact-checks talking points.",
    version="1.0.0",
)

# Allow the Streamlit frontend (typically on localhost:8501) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database initialized.")


@app.get("/")
def root():
    return {"status": "ok", "service": "Personalized Networking Assistant API"}


@app.post("/api/v1/generate", response_model=GenerateResponse)
def generate_starters(payload: GenerateRequest, db: Session = Depends(get_db)):
    try:
        themes = nlp_service.extract_themes(payload.event_description)
        starters = nlp_service.generate_conversation_starters(
            themes=themes,
            interests=payload.interests,
            bio=payload.bio or "",
            num_starters=payload.num_starters,
        )
    except Exception as exc:
        logger.exception("Generation failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")

    log_entry = InteractionLog(
        event_description=payload.event_description,
        interests=", ".join(payload.interests),
        extracted_themes=", ".join(themes),
        generated_starters=json.dumps(starters),
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return GenerateResponse(
        interaction_id=log_entry.id,
        extracted_themes=themes,
        conversation_starters=starters,
    )


@app.get("/api/v1/verify", response_model=VerifyResponse)
def verify_fact(query: str, interaction_id: int | None = None, db: Session = Depends(get_db)):
    result = factcheck_service.fact_check(query)

    if interaction_id is not None:
        log_entry = db.query(InteractionLog).filter(InteractionLog.id == interaction_id).first()
        if log_entry:
            log_entry.fact_check_query = result["query"]
            log_entry.fact_check_result = result["summary"]
            db.commit()

    return VerifyResponse(**result)


@app.post("/api/v1/feedback")
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    log_entry = db.query(InteractionLog).filter(InteractionLog.id == payload.interaction_id).first()
    if not log_entry:
        raise HTTPException(status_code=404, detail="Interaction not found")
    log_entry.feedback = payload.useful
    db.commit()
    return {"status": "ok", "interaction_id": payload.interaction_id, "feedback": payload.useful}


@app.get("/api/v1/history", response_model=HistoryResponse)
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(InteractionLog)
        .order_by(InteractionLog.created_at.desc())
        .limit(limit)
        .all()
    )
    items = [
        HistoryItem(
            id=row.id,
            event_description=row.event_description,
            extracted_themes=(row.extracted_themes or "").split(", ") if row.extracted_themes else [],
            generated_starters=json.loads(row.generated_starters) if row.generated_starters else [],
            fact_check_query=row.fact_check_query,
            fact_check_result=row.fact_check_result,
            feedback=row.feedback,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]
    return HistoryResponse(items=items)
