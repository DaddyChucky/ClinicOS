from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.marketing_content_agent import run_marketing_content
from app.agents.marketing_strategist_agent import run_marketing_strategist
from app.database import get_db
from app.models.enums import DraftStatus
from app.models.schemas import CampaignDraftRead, DeleteResultRead, MarketingGenerateRequest, ReviewActionRequest
from app.repositories.draft_repository import DraftRepository
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/marketing", tags=["marketing"])


@router.post("/generate", response_model=CampaignDraftRead)
async def generate_marketing(payload: MarketingGenerateRequest, db: Session = Depends(get_db)):
    segment_pains = []
    if payload.segment_notes:
        segment_pains = [note.strip() for note in payload.segment_notes.split(",") if note.strip()]

    strategist = await run_marketing_strategist(
        user_message=f"Generate strategy for {payload.audience}",
        audience=payload.audience,
        pain_points=segment_pains or ["insurance delays", "schedule gaps", "manual follow-up"],
    )

    content = await run_marketing_content(
        audience=payload.audience,
        objective=payload.objective,
        pain_points=segment_pains or strategist.opportunities[:2],
    )

    draft = DraftRepository(db).create_campaign_draft(
        conversation_id=payload.conversation_id,
        title=content.title,
        audience=payload.audience,
        channel=content.channel,
        brief=f"{content.brief}\n\nStrategy note: {strategist.recommendation}",
        nurture_sequence=content.nurture_sequence,
        status=DraftStatus.APPROVED if payload.conversation_id is None else DraftStatus.PENDING_REVIEW,
        review_required=payload.conversation_id is not None,
    )
    return draft


@router.get("/drafts", response_model=list[CampaignDraftRead])
def list_drafts(db: Session = Depends(get_db)):
    return DraftRepository(db).list_campaign_drafts(admin_only=True)


@router.delete("/plans/{draft_id}", response_model=DeleteResultRead)
def delete_campaign_plan(draft_id: int, db: Session = Depends(get_db)):
    deleted = DraftRepository(db).delete_campaign_draft(draft_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Campaign plan not found")
    return DeleteResultRead(id=draft_id, deleted=True)


@router.post("/drafts/{draft_id}/approve", response_model=CampaignDraftRead)
def approve_draft(draft_id: int, payload: ReviewActionRequest, db: Session = Depends(get_db)):
    review_service = ReviewService(db)
    draft, _ = review_service.approve_campaign(draft_id, payload.reviewer_name, payload.notes)
    if not draft:
        raise HTTPException(status_code=404, detail="Campaign draft not found")
    return draft


@router.post("/drafts/{draft_id}/reject", response_model=CampaignDraftRead)
def reject_draft(draft_id: int, payload: ReviewActionRequest, db: Session = Depends(get_db)):
    review_service = ReviewService(db)
    draft, _ = review_service.reject_campaign(draft_id, payload.reviewer_name, payload.notes)
    if not draft:
        raise HTTPException(status_code=404, detail="Campaign draft not found")
    return draft
