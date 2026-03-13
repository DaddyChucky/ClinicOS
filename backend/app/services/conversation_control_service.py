from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import db_models
from app.models.enums import ConversationStatus
from app.models.schemas import (
    ConversationControlRead,
    ConversationControlUpdateRequest,
    ConversationDeletionRead,
    PracticeProfileUpdateRequest,
)
from app.repositories.conversation_repository import ConversationRepository
from app.services.case_service import CaseService


class ConversationControlService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ConversationRepository(db)
        self.case_service = CaseService()

    def get_or_create_control(self, conversation_id: int) -> db_models.ConversationControl:
        stmt = select(db_models.ConversationControl).where(db_models.ConversationControl.conversation_id == conversation_id)
        control = self.db.scalar(stmt)
        if control:
            return control

        control = db_models.ConversationControl(conversation_id=conversation_id)
        self.db.add(control)
        self.db.commit()
        self.db.refresh(control)
        return control

    def get_or_create_system_control(self) -> db_models.SystemControl:
        stmt = select(db_models.SystemControl).order_by(db_models.SystemControl.id.asc()).limit(1)
        control = self.db.scalar(stmt)
        if control:
            return control

        control = db_models.SystemControl(global_agent_enabled=True)
        self.db.add(control)
        self.db.commit()
        self.db.refresh(control)
        return control

    def update_control(
        self,
        conversation_id: int,
        payload: ConversationControlUpdateRequest,
    ) -> tuple[db_models.ConversationControl, db_models.SystemControl]:
        conversation = self.repo.get_conversation(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        control = self.get_or_create_control(conversation_id)
        system_control = self.get_or_create_system_control()
        chat_name = conversation.title or f"Practice Desk Chat #{conversation.id}"

        if payload.active_chat_enabled is not None and control.assistant_active != payload.active_chat_enabled:
            control.assistant_active = payload.active_chat_enabled
            control.triage_active = payload.active_chat_enabled
            conversation.updated_at = db_models.utc_now()
            self.db.add(
                db_models.ConversationEventLog(
                    conversation_id=conversation_id,
                    stage="Active Chat Power Switch",
                    detail=(
                        f"{chat_name} is Live."
                        if payload.active_chat_enabled
                        else f"{chat_name} is Offline."
                    ),
                    status="live" if payload.active_chat_enabled else "offline",
                    meta_json={
                        "scope": "active_chat",
                        "power_state": "live" if payload.active_chat_enabled else "offline",
                    },
                )
            )

        if payload.global_agent_enabled is not None and system_control.global_agent_enabled != payload.global_agent_enabled:
            system_control.global_agent_enabled = payload.global_agent_enabled
            affected_conversation_ids = self.db.scalars(
                select(db_models.Conversation.id).where(~db_models.Conversation.deletion_record.has())
            ).all()
            for affected_id in affected_conversation_ids:
                self.db.add(
                    db_models.ConversationEventLog(
                        conversation_id=affected_id,
                        stage="All Chats Power Switch",
                        detail=(
                            "All Chats are switched On."
                            if payload.global_agent_enabled
                            else "All Chats are switched Off."
                        ),
                        status="live" if payload.global_agent_enabled else "offline",
                        meta_json={
                            "scope": "all_chats",
                            "power_state": "live" if payload.global_agent_enabled else "offline",
                        },
                    )
                )
            if affected_conversation_ids:
                for active_conversation in self.db.scalars(
                    select(db_models.Conversation).where(db_models.Conversation.id.in_(affected_conversation_ids))
                ):
                    active_conversation.updated_at = db_models.utc_now()

        self.db.commit()
        self.db.refresh(control)
        self.db.refresh(system_control)
        return control, system_control

    def get_or_create_profile_override(self, conversation_id: int) -> db_models.ConversationProfileOverride:
        stmt = select(db_models.ConversationProfileOverride).where(
            db_models.ConversationProfileOverride.conversation_id == conversation_id
        )
        profile_override = self.db.scalar(stmt)
        if profile_override:
            return profile_override

        profile_override = db_models.ConversationProfileOverride(conversation_id=conversation_id)
        self.db.add(profile_override)
        self.db.commit()
        self.db.refresh(profile_override)
        return profile_override

    def update_profile_override(
        self,
        conversation_id: int,
        payload: PracticeProfileUpdateRequest,
    ) -> db_models.ConversationProfileOverride:
        profile_override = self.get_or_create_profile_override(conversation_id)
        for field in PracticeProfileUpdateRequest.model_fields:
            if hasattr(profile_override, field):
                setattr(profile_override, field, getattr(payload, field))
        self.db.commit()
        self.db.refresh(profile_override)
        return profile_override

    def soft_delete_conversation(self, conversation_id: int, deleted_by: str) -> ConversationDeletionRead:
        conversation = self.repo.get_conversation_with_context(conversation_id, include_deleted=True)
        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.deletion_record:
            return ConversationDeletionRead.model_validate(conversation.deletion_record)

        snapshot = self.case_service.build_case_snapshot(conversation)
        snapshot.controls = self.to_read(
            self.get_or_create_control(conversation_id),
            self.get_or_create_system_control(),
        )
        archive_event = {
            "id": None,
            "stage": "Delete Chat Action",
            "detail": f"Chat was deleted by {deleted_by.title()} and moved into the audit archive.",
            "status": "offline",
            "created_at": db_models.utc_now().isoformat(),
        }
        archive_payload = {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "status": conversation.status,
            "deleted_by": deleted_by.title(),
            "case_snapshot": snapshot.model_dump(mode="json"),
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "agent_name": message.agent_name,
                    "workflow": message.workflow,
                    "created_at": message.created_at.isoformat(),
                }
                for message in conversation.messages
            ],
            "runs": [
                {
                    "id": run.id,
                    "agent_name": run.agent_name,
                    "workflow": run.workflow,
                    "confidence": run.confidence,
                    "output_text": run.output_text,
                    "created_at": run.created_at.isoformat(),
                }
                for run in conversation.runs
            ],
            "event_logs": [
                {
                    "id": event.id,
                    "stage": event.stage,
                    "detail": event.detail,
                    "status": event.status,
                    "created_at": event.created_at.isoformat(),
                }
                for event in sorted(conversation.event_logs, key=lambda item: item.created_at, reverse=True)
            ]
            + [archive_event],
        }
        summary = conversation.title or f"Practice Desk Chat #{conversation.id}"

        deletion = db_models.ConversationDeletion(
            conversation_id=conversation.id,
            title=conversation.title,
            deleted_by=deleted_by.lower(),
            summary=f"{summary} was deleted by {deleted_by.title()} and archived for audit review.",
            snapshot_json=archive_payload,
        )
        conversation.status = ConversationStatus.CLOSED
        conversation.updated_at = db_models.utc_now()
        self.db.add(
            db_models.ConversationEventLog(
                conversation_id=conversation.id,
                stage=archive_event["stage"],
                detail=archive_event["detail"],
                status=archive_event["status"],
                meta_json={"deleted_by": deleted_by.lower()},
            )
        )
        self.db.add(deletion)
        self.db.commit()
        self.db.refresh(deletion)
        return ConversationDeletionRead.model_validate(deletion)

    def list_deleted_conversations(self, limit: int = 50) -> list[ConversationDeletionRead]:
        return [
            ConversationDeletionRead.model_validate(item)
            for item in self.repo.list_deleted_conversations(limit=limit)
        ]

    def workspace_message(self, control: db_models.ConversationControl, system_control: db_models.SystemControl) -> str | None:
        if not system_control.global_agent_enabled:
            return "Practice Desk is temporarily unavailable because an admin powered off ClinicOS AI for all chats."
        if not control.assistant_active:
            return "Practice Desk is temporarily unavailable because an admin suspended this chat."
        return None

    def to_read(
        self,
        control: db_models.ConversationControl,
        system_control: db_models.SystemControl | None = None,
    ) -> ConversationControlRead:
        global_control = system_control or self.get_or_create_system_control()
        workspace_available = bool(control.assistant_active and global_control.global_agent_enabled)
        return ConversationControlRead(
            active_chat_enabled=bool(control.assistant_active),
            global_agent_enabled=bool(global_control.global_agent_enabled),
            workspace_available=workspace_available,
            admin_message=self.workspace_message(control, global_control),
            updated_at=control.updated_at,
            global_updated_at=global_control.updated_at,
        )
