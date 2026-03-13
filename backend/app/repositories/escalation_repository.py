from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import db_models
from app.models.enums import EscalationStatus


class EscalationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        conversation_id: int,
        summary: str,
        reason: str,
        created_by_agent: str | None = None,
        status: EscalationStatus = EscalationStatus.OPEN,
    ) -> db_models.Escalation:
        escalation = db_models.Escalation(
            conversation_id=conversation_id,
            summary=summary,
            reason=reason,
            created_by_agent=created_by_agent,
            status=status,
        )
        self.db.add(escalation)
        self.db.commit()
        self.db.refresh(escalation)
        return escalation

    def list_all(self) -> list[db_models.Escalation]:
        stmt = select(db_models.Escalation).order_by(db_models.Escalation.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def list_active(self) -> list[db_models.Escalation]:
        stmt = (
            select(db_models.Escalation)
            .join(db_models.Conversation, db_models.Conversation.id == db_models.Escalation.conversation_id)
            .where(db_models.Escalation.status.in_([EscalationStatus.OPEN, EscalationStatus.IN_PROGRESS]))
            .where(~db_models.Conversation.deletion_record.has())
            .order_by(db_models.Escalation.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get(self, escalation_id: int) -> db_models.Escalation | None:
        return self.db.get(db_models.Escalation, escalation_id)

    def get_active_for_conversation(self, conversation_id: int) -> db_models.Escalation | None:
        stmt = (
            select(db_models.Escalation)
            .join(db_models.Conversation, db_models.Conversation.id == db_models.Escalation.conversation_id)
            .where(
                db_models.Escalation.conversation_id == conversation_id,
                db_models.Escalation.status.in_([EscalationStatus.OPEN, EscalationStatus.IN_PROGRESS]),
            )
            .where(~db_models.Conversation.deletion_record.has())
            .order_by(db_models.Escalation.created_at.desc())
        )
        return self.db.scalar(stmt)

    def update_status(
        self,
        escalation: db_models.Escalation,
        status: EscalationStatus,
    ) -> db_models.Escalation:
        escalation.status = status
        self.db.commit()
        self.db.refresh(escalation)
        return escalation
