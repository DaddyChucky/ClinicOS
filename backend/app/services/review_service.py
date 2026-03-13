from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import DraftStatus, ReviewDecisionType, ReviewEntityType
from app.repositories.draft_repository import DraftRepository


class ReviewService:
    def __init__(self, db: Session):
        self.repo = DraftRepository(db)

    def approve_outreach(self, draft_id: int, reviewer_name: str, notes: str | None):
        draft = self.repo.get_outreach_draft(draft_id)
        if not draft:
            return None, None
        updated = self.repo.update_outreach_status(draft, DraftStatus.APPROVED)
        decision = self.repo.create_review_decision(
            entity_type=ReviewEntityType.OUTREACH,
            entity_id=draft_id,
            decision=ReviewDecisionType.APPROVE,
            reviewer_name=reviewer_name,
            notes=notes,
        )
        return updated, decision

    def reject_outreach(self, draft_id: int, reviewer_name: str, notes: str | None):
        draft = self.repo.get_outreach_draft(draft_id)
        if not draft:
            return None, None
        updated = self.repo.update_outreach_status(draft, DraftStatus.REJECTED)
        decision = self.repo.create_review_decision(
            entity_type=ReviewEntityType.OUTREACH,
            entity_id=draft_id,
            decision=ReviewDecisionType.REJECT,
            reviewer_name=reviewer_name,
            notes=notes,
        )
        return updated, decision

    def approve_campaign(self, draft_id: int, reviewer_name: str, notes: str | None):
        draft = self.repo.get_campaign_draft(draft_id)
        if not draft:
            return None, None
        updated = self.repo.update_campaign_status(draft, DraftStatus.APPROVED)
        decision = self.repo.create_review_decision(
            entity_type=ReviewEntityType.CAMPAIGN,
            entity_id=draft_id,
            decision=ReviewDecisionType.APPROVE,
            reviewer_name=reviewer_name,
            notes=notes,
        )
        return updated, decision

    def reject_campaign(self, draft_id: int, reviewer_name: str, notes: str | None):
        draft = self.repo.get_campaign_draft(draft_id)
        if not draft:
            return None, None
        updated = self.repo.update_campaign_status(draft, DraftStatus.REJECTED)
        decision = self.repo.create_review_decision(
            entity_type=ReviewEntityType.CAMPAIGN,
            entity_id=draft_id,
            decision=ReviewDecisionType.REJECT,
            reviewer_name=reviewer_name,
            notes=notes,
        )
        return updated, decision
