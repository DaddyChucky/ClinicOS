from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import EscalationCreateRequest, EscalationRead
from app.repositories.escalation_repository import EscalationRepository
from app.services.escalation_service import EscalationService

router = APIRouter(prefix="/api/escalations", tags=["escalations"])


@router.post("/create", response_model=EscalationRead)
def create_escalation(payload: EscalationCreateRequest, db: Session = Depends(get_db)):
    service = EscalationService(db)
    escalation = service.create_escalation(
        conversation_id=payload.conversation_id,
        reason=payload.reason,
        summary=payload.summary,
        created_by_agent=payload.created_by_agent,
    )
    return escalation


@router.get("", response_model=list[EscalationRead])
def list_escalations(db: Session = Depends(get_db)):
    repo = EscalationRepository(db)
    return repo.list_all()


@router.get("/{escalation_id}", response_model=EscalationRead)
def get_escalation(escalation_id: int, db: Session = Depends(get_db)):
    repo = EscalationRepository(db)
    escalation = repo.get(escalation_id)
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return escalation
