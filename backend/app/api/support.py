from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import EscalationRead, HumanSupportQueueItemRead, HumanSupportReplyRequest, MessageRead
from app.services.escalation_service import EscalationService

router = APIRouter(prefix="/api/support", tags=["support"])


@router.post("/{conversation_id}/talk-to-human", response_model=EscalationRead)
def talk_to_human(conversation_id: int, db: Session = Depends(get_db)):
    service = EscalationService(db)
    escalation = service.create_escalation(
        conversation_id=conversation_id,
        reason="User requested human support",
        summary=None,
        created_by_agent="ClinicOS AI Triage Agent",
    )
    queue_item = service.get_queue_item(conversation_id)
    return EscalationRead.model_validate(escalation).model_copy(
        update={"queue_position": queue_item.queue_position if queue_item else None}
    )


@router.get("/queue", response_model=list[HumanSupportQueueItemRead])
def list_support_queue(db: Session = Depends(get_db)):
    return EscalationService(db).list_queue_items()


@router.get("/{conversation_id}/status", response_model=HumanSupportQueueItemRead)
def get_support_status(conversation_id: int, db: Session = Depends(get_db)):
    item = EscalationService(db).get_queue_item(conversation_id)
    if not item:
        raise HTTPException(status_code=404, detail="No active human support request exists for this chat")
    return item


@router.post("/{conversation_id}/reply", response_model=MessageRead)
def reply_to_chat(conversation_id: int, payload: HumanSupportReplyRequest, db: Session = Depends(get_db)):
    service = EscalationService(db)
    try:
        return service.human_reply(
            conversation_id=conversation_id,
            message=payload.message,
            responder_name=payload.responder_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{conversation_id}/take-over", response_model=HumanSupportQueueItemRead)
def take_over_chat(conversation_id: int, db: Session = Depends(get_db)):
    service = EscalationService(db)
    try:
        return service.take_over(conversation_id=conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
