from __future__ import annotations

import pytest

from app.api.review import review_queue
from app.api.sales import approve_draft, sales_research
from app.models.schemas import ReviewActionRequest, SalesResearchRequest

@pytest.mark.asyncio
async def test_review_approval_flow_for_outreach(db_session):
    response = await sales_research(
        SalesResearchRequest(
            clinic_name="Sunrise Family Dental",
            location="Austin, TX",
        ),
        db_session,
    )
    draft_id = response.outreach_draft.id

    approve = approve_draft(
        draft_id,
        ReviewActionRequest(reviewer_name="QA Reviewer", notes="Approved"),
        db_session,
    )
    assert approve.status == "approved"

    queue = review_queue(db_session)
    assert all(item["draft_id"] != draft_id for item in queue)
