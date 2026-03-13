from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import db_models
from app.models.enums import DraftStatus, ReviewDecisionType, ReviewEntityType


class DraftRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_outreach_draft(
        self,
        prospect_id: int,
        conversation_id: int | None,
        subject: str,
        body: str,
        tone: str,
        personalization_notes: str | None,
        *,
        status: DraftStatus = DraftStatus.PENDING_REVIEW,
        review_required: bool = True,
    ) -> db_models.OutreachDraft:
        draft = db_models.OutreachDraft(
            prospect_id=prospect_id,
            conversation_id=conversation_id,
            subject=subject,
            body=body,
            tone=tone,
            personalization_notes=personalization_notes,
            status=status,
            review_required=review_required,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def list_outreach_drafts(self, *, admin_only: bool = False) -> list[db_models.OutreachDraft]:
        stmt = select(db_models.OutreachDraft)
        if admin_only:
            stmt = stmt.where(db_models.OutreachDraft.conversation_id.is_(None))
        stmt = stmt.order_by(db_models.OutreachDraft.updated_at.desc())
        return list(self.db.scalars(stmt).all())

    def list_outreach_history(self, *, admin_only: bool = False) -> list[db_models.OutreachDraft]:
        stmt = (
            select(db_models.OutreachDraft)
            .options(joinedload(db_models.OutreachDraft.prospect))
        )
        if admin_only:
            stmt = stmt.where(db_models.OutreachDraft.conversation_id.is_(None))
        stmt = stmt.order_by(db_models.OutreachDraft.updated_at.desc())
        return list(self.db.scalars(stmt).unique().all())

    def get_outreach_draft(self, draft_id: int) -> db_models.OutreachDraft | None:
        return self.db.get(db_models.OutreachDraft, draft_id)

    def delete_outreach_history(self, draft_id: int) -> bool:
        draft = self.get_outreach_draft(draft_id)
        if not draft or draft.conversation_id is not None:
            return False

        prospect = draft.prospect
        self.db.delete(draft)
        self.db.flush()

        if prospect is not None:
            remaining = self.db.scalar(
                select(db_models.OutreachDraft.id)
                .where(db_models.OutreachDraft.prospect_id == prospect.id)
                .limit(1)
            )
            if remaining is None:
                self.db.delete(prospect)

        self.db.commit()
        return True

    def update_outreach_status(self, draft: db_models.OutreachDraft, status: DraftStatus) -> db_models.OutreachDraft:
        draft.status = status
        draft.review_required = status == DraftStatus.PENDING_REVIEW
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def create_campaign_draft(
        self,
        conversation_id: int | None,
        title: str,
        audience: str,
        channel: str,
        brief: str,
        nurture_sequence: list[dict] | None,
        *,
        status: DraftStatus = DraftStatus.PENDING_REVIEW,
        review_required: bool = True,
    ) -> db_models.CampaignDraft:
        draft = db_models.CampaignDraft(
            conversation_id=conversation_id,
            title=title,
            audience=audience,
            channel=channel,
            brief=brief,
            nurture_sequence_json=nurture_sequence,
            status=status,
            review_required=review_required,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def list_campaign_drafts(self, *, admin_only: bool = False) -> list[db_models.CampaignDraft]:
        stmt = select(db_models.CampaignDraft)
        if admin_only:
            stmt = stmt.where(db_models.CampaignDraft.conversation_id.is_(None))
        stmt = stmt.order_by(db_models.CampaignDraft.updated_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_campaign_draft(self, draft_id: int) -> db_models.CampaignDraft | None:
        return self.db.get(db_models.CampaignDraft, draft_id)

    def delete_campaign_draft(self, draft_id: int) -> bool:
        draft = self.get_campaign_draft(draft_id)
        if not draft or draft.conversation_id is not None:
            return False

        self.db.delete(draft)
        self.db.commit()
        return True

    def update_campaign_status(self, draft: db_models.CampaignDraft, status: DraftStatus) -> db_models.CampaignDraft:
        draft.status = status
        draft.review_required = status == DraftStatus.PENDING_REVIEW
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def create_review_decision(
        self,
        entity_type: ReviewEntityType,
        entity_id: int,
        decision: ReviewDecisionType,
        reviewer_name: str,
        notes: str | None,
    ) -> db_models.ReviewDecision:
        review = db_models.ReviewDecision(
            entity_type=entity_type,
            entity_id=entity_id,
            decision=decision,
            reviewer_name=reviewer_name,
            notes=notes,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_review_queue(self) -> list[dict]:
        items: list[dict] = []
        outreach_stmt = select(db_models.OutreachDraft).where(
            db_models.OutreachDraft.review_required.is_(True),
            db_models.OutreachDraft.conversation_id.is_not(None),
        )
        campaign_stmt = select(db_models.CampaignDraft).where(
            db_models.CampaignDraft.review_required.is_(True),
            db_models.CampaignDraft.conversation_id.is_not(None),
        )

        for draft in self.db.scalars(outreach_stmt):
            items.append(
                {
                    "entity_type": ReviewEntityType.OUTREACH,
                    "draft_id": draft.id,
                    "conversation_id": draft.conversation_id,
                    "title": draft.subject,
                    "status": draft.status,
                    "review_required": draft.review_required,
                    "created_at": draft.created_at,
                }
            )

        for draft in self.db.scalars(campaign_stmt):
            items.append(
                {
                    "entity_type": ReviewEntityType.CAMPAIGN,
                    "draft_id": draft.id,
                    "conversation_id": draft.conversation_id,
                    "title": draft.title,
                    "status": draft.status,
                    "review_required": draft.review_required,
                    "created_at": draft.created_at,
                }
            )

        items.sort(key=lambda x: x["created_at"], reverse=True)
        return items
