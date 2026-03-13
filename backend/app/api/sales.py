from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.sales_outreach_agent import run_sales_outreach
from app.agents.sales_research_agent import run_sales_research
from app.database import get_db
from app.models.enums import DraftStatus
from app.models.schemas import (
    DeleteResultRead,
    OutreachDraftRead,
    ReviewActionRequest,
    SalesResearchRequest,
    SalesResearchHistoryItemRead,
    SalesResearchResponse,
)
from app.repositories.draft_repository import DraftRepository
from app.repositories.prospect_repository import ProspectRepository
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.post("/research", response_model=SalesResearchResponse)
async def sales_research(payload: SalesResearchRequest, db: Session = Depends(get_db)):
    research = await run_sales_research(
        user_message=f"Research clinic {payload.clinic_name}",
        clinic_name=payload.clinic_name,
        location=payload.location,
    )

    prospect = ProspectRepository(db).create_or_update(
        clinic_name=research.profile["clinic_name"],
        clinic_type=research.profile["clinic_type"],
        conversation_id=payload.conversation_id,
        specialty=research.profile.get("specialty"),
        size_estimate=research.profile.get("size_estimate"),
        location=research.profile.get("location"),
        existing_lead=research.profile.get("existing_lead", False),
        fit_score=research.fit_score,
        pain_points=research.profile.get("pain_points", []),
        research_summary=research.summary,
    )

    outreach = await run_sales_outreach(research.profile, research.fit_score, research.fit_reasons)
    draft = DraftRepository(db).create_outreach_draft(
        prospect_id=prospect.id,
        conversation_id=payload.conversation_id,
        subject=outreach.subject,
        body=outreach.body,
        tone=outreach.tone,
        personalization_notes=outreach.personalization_notes,
        status=DraftStatus.APPROVED if payload.conversation_id is None else DraftStatus.PENDING_REVIEW,
        review_required=payload.conversation_id is not None,
    )
    return SalesResearchResponse(
        prospect=prospect,
        fit_score=research.fit_score,
        fit_reasons=research.fit_reasons,
        summary=research.summary,
        outreach_draft=draft,
    )


@router.get("/history", response_model=list[SalesResearchHistoryItemRead])
def sales_research_history(db: Session = Depends(get_db)):
    items = DraftRepository(db).list_outreach_history(admin_only=True)
    history: list[SalesResearchHistoryItemRead] = []
    for item in items:
        prospect = item.prospect
        if not prospect:
            continue
        history.append(
            SalesResearchHistoryItemRead(
                id=item.id,
                clinic_name=prospect.clinic_name,
                clinic_type=prospect.clinic_type,
                specialty=prospect.specialty,
                size_estimate=prospect.size_estimate,
                location=prospect.location,
                existing_lead=prospect.existing_lead,
                fit_score=prospect.fit_score,
                pain_points_json=prospect.pain_points_json,
                research_summary=prospect.research_summary,
                outreach_subject=item.subject,
                outreach_body=item.body,
                personalization_notes=item.personalization_notes,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )
    return history


@router.get("/drafts", response_model=list[OutreachDraftRead])
def list_drafts(db: Session = Depends(get_db)):
    return DraftRepository(db).list_outreach_drafts(admin_only=True)


@router.delete("/history/{draft_id}", response_model=DeleteResultRead)
def delete_history_item(draft_id: int, db: Session = Depends(get_db)):
    deleted = DraftRepository(db).delete_outreach_history(draft_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sales research history item not found")
    return DeleteResultRead(id=draft_id, deleted=True)


@router.post("/drafts/{draft_id}/approve", response_model=OutreachDraftRead)
def approve_draft(draft_id: int, payload: ReviewActionRequest, db: Session = Depends(get_db)):
    review_service = ReviewService(db)
    draft, _ = review_service.approve_outreach(draft_id, payload.reviewer_name, payload.notes)
    if not draft:
        raise HTTPException(status_code=404, detail="Outreach draft not found")
    return draft


@router.post("/drafts/{draft_id}/reject", response_model=OutreachDraftRead)
def reject_draft(draft_id: int, payload: ReviewActionRequest, db: Session = Depends(get_db)):
    review_service = ReviewService(db)
    draft, _ = review_service.reject_outreach(draft_id, payload.reviewer_name, payload.notes)
    if not draft:
        raise HTTPException(status_code=404, detail="Outreach draft not found")
    return draft
