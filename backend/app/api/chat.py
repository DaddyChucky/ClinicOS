from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import (
    CaseSnapshotRead,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatStartRequest,
    ConversationControlRead,
    ConversationControlUpdateRequest,
    ConversationDeletionRead,
    ConversationRead,
    ConversationSummaryRead,
    PracticeProfileUpdateRequest,
)
from app.repositories.conversation_repository import ConversationRepository
from app.services.case_service import CaseService
from app.services.conversation_control_service import ConversationControlService
from app.workflows.orchestrator import WorkflowOrchestrator

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/start", response_model=ConversationRead)
async def start_chat(payload: ChatStartRequest, db: Session = Depends(get_db)):
    orchestrator = WorkflowOrchestrator(db)
    conversation = await orchestrator.start_conversation(
        user_name=payload.user_name,
        user_email=payload.user_email,
        opening_message=payload.opening_message,
    )
    conversation = ConversationRepository(db).get_conversation(conversation.id)
    if not conversation:
        raise HTTPException(status_code=500, detail="Failed to create conversation")
    return conversation


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(payload: ChatMessageRequest, db: Session = Depends(get_db)):
    orchestrator = WorkflowOrchestrator(db)
    return await orchestrator.process_message(payload.conversation_id, payload.message)


@router.get("/conversations", response_model=list[ConversationSummaryRead])
async def list_conversations(
    user_email: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    repo = ConversationRepository(db)
    conversations = repo.list_conversations(user_email=user_email, limit=limit)
    items: list[ConversationSummaryRead] = []
    for conversation in conversations:
        non_system_messages = [message for message in conversation.messages if message.role != "system"]
        source_messages = non_system_messages or conversation.messages
        last_message = max(source_messages, key=lambda message: message.created_at, default=None)
        preview = None
        if last_message:
            preview = last_message.content.strip().replace("\n", " ")
            if len(preview) > 140:
                preview = f"{preview[:137]}..."
        items.append(
            ConversationSummaryRead(
                id=conversation.id,
                title=conversation.title,
                updated_at=conversation.updated_at,
                last_message_preview=preview,
            )
        )
    return items


@router.get("/deleted/archive", response_model=list[ConversationDeletionRead])
async def list_deleted_thread_archive(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ConversationControlService(db).list_deleted_conversations(limit=limit)


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_chat(conversation_id: int, db: Session = Depends(get_db)):
    conversation = ConversationRepository(db).get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/{conversation_id}/case", response_model=CaseSnapshotRead)
async def get_case_snapshot(conversation_id: int, db: Session = Depends(get_db)):
    conversation = ConversationRepository(db).get_conversation_with_context(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    snapshot = CaseService().build_case_snapshot(conversation)
    control_service = ConversationControlService(db)
    snapshot.controls = control_service.to_read(control_service.get_or_create_control(conversation_id))
    return snapshot


@router.put("/{conversation_id}/controls", response_model=ConversationControlRead)
async def update_conversation_controls(
    conversation_id: int,
    payload: ConversationControlUpdateRequest,
    db: Session = Depends(get_db),
):
    conversation = ConversationRepository(db).get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    service = ConversationControlService(db)
    control, system_control = service.update_control(conversation_id, payload)
    return service.to_read(control, system_control)


@router.put("/{conversation_id}/profile", response_model=CaseSnapshotRead)
async def update_practice_profile(
    conversation_id: int,
    payload: PracticeProfileUpdateRequest,
    db: Session = Depends(get_db),
):
    repo = ConversationRepository(db)
    conversation = repo.get_conversation_with_context(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    control_service = ConversationControlService(db)
    control_service.update_profile_override(conversation_id, payload)
    refreshed = repo.get_conversation_with_context(conversation_id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="Conversation not found")

    snapshot = CaseService().build_case_snapshot(refreshed)
    snapshot.controls = control_service.to_read(control_service.get_or_create_control(conversation_id))
    return snapshot


@router.delete("/{conversation_id}", response_model=ConversationDeletionRead)
async def delete_conversation(
    conversation_id: int,
    deleted_by: str = Query(default="user", pattern="^(user|admin)$"),
    db: Session = Depends(get_db),
):
    repo = ConversationRepository(db)
    conversation = repo.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        return ConversationControlService(db).soft_delete_conversation(conversation_id, deleted_by=deleted_by)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
