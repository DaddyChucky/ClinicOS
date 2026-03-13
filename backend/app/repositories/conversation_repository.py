from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import db_models


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, email: str, name: str, role: str = "internal") -> db_models.User:
        stmt = select(db_models.User).where(db_models.User.email == email)
        user = self.db.scalar(stmt)
        if user:
            if user.name != name:
                user.name = name
                self.db.commit()
                self.db.refresh(user)
            return user

        user = db_models.User(email=email, name=name, role=role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_conversation(self, user_id: int | None, title: str | None = None) -> db_models.Conversation:
        conversation = db_models.Conversation(user_id=user_id, title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: int, *, include_deleted: bool = False) -> db_models.Conversation | None:
        stmt = (
            select(db_models.Conversation)
            .where(db_models.Conversation.id == conversation_id)
            .options(
                joinedload(db_models.Conversation.user),
                joinedload(db_models.Conversation.messages),
                joinedload(db_models.Conversation.control),
                joinedload(db_models.Conversation.profile_override),
                joinedload(db_models.Conversation.event_logs),
                joinedload(db_models.Conversation.deletion_record),
            )
        )
        if not include_deleted:
            stmt = stmt.where(~db_models.Conversation.deletion_record.has())
        return self.db.scalars(stmt).unique().one_or_none()

    def get_conversation_with_context(
        self,
        conversation_id: int,
        *,
        include_deleted: bool = False,
    ) -> db_models.Conversation | None:
        stmt = (
            select(db_models.Conversation)
            .where(db_models.Conversation.id == conversation_id)
            .options(
                joinedload(db_models.Conversation.user),
                joinedload(db_models.Conversation.messages),
                joinedload(db_models.Conversation.runs),
                joinedload(db_models.Conversation.escalations),
                joinedload(db_models.Conversation.prospects),
                joinedload(db_models.Conversation.outreach_drafts),
                joinedload(db_models.Conversation.campaign_drafts),
                joinedload(db_models.Conversation.control),
                joinedload(db_models.Conversation.profile_override),
                joinedload(db_models.Conversation.event_logs),
                joinedload(db_models.Conversation.deletion_record),
            )
        )
        if not include_deleted:
            stmt = stmt.where(~db_models.Conversation.deletion_record.has())
        return self.db.scalars(stmt).unique().one_or_none()

    def list_conversations(self, user_email: str | None = None, limit: int = 25) -> list[db_models.Conversation]:
        user_id: int | None = None
        if user_email:
            user_stmt = select(db_models.User).where(db_models.User.email == user_email)
            user = self.db.scalar(user_stmt)
            if not user:
                return []
            user_id = user.id

        stmt = (
            select(db_models.Conversation)
            .where(~db_models.Conversation.deletion_record.has())
            .options(joinedload(db_models.Conversation.messages))
        )
        if user_id is not None:
            stmt = stmt.where(db_models.Conversation.user_id == user_id)
        stmt = stmt.order_by(db_models.Conversation.updated_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).unique().all())

    def list_deleted_conversations(self, limit: int = 50) -> list[db_models.ConversationDeletion]:
        stmt = (
            select(db_models.ConversationDeletion)
            .options(joinedload(db_models.ConversationDeletion.conversation))
            .order_by(db_models.ConversationDeletion.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        agent_name: str | None = None,
        workflow: str | None = None,
        confidence: float | None = None,
        meta_json: dict | None = None,
    ) -> db_models.Message:
        message = db_models.Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_name=agent_name,
            workflow=workflow,
            confidence=confidence,
            meta_json=meta_json,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def add_run_log(
        self,
        conversation_id: int,
        agent_name: str,
        workflow: str,
        input_text: str,
        output_text: str,
        confidence: float,
        handoff_to: str | None = None,
        escalation_recommended: bool = False,
        tool_trace_json: dict | None = None,
    ) -> db_models.AgentRun:
        run = db_models.AgentRun(
            conversation_id=conversation_id,
            agent_name=agent_name,
            workflow=workflow,
            input_text=input_text,
            output_text=output_text,
            confidence=confidence,
            handoff_to=handoff_to,
            escalation_recommended=escalation_recommended,
            tool_trace_json=tool_trace_json,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_conversation_state(self, conversation: db_models.Conversation, **updates: object) -> db_models.Conversation:
        for key, value in updates.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def add_event_log(
        self,
        conversation_id: int,
        stage: str,
        detail: str,
        status: str = "live",
        meta_json: dict | None = None,
    ) -> db_models.ConversationEventLog:
        event = db_models.ConversationEventLog(
            conversation_id=conversation_id,
            stage=stage,
            detail=detail,
            status=status,
            meta_json=meta_json,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
