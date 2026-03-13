from __future__ import annotations

import pytest

from app.agents.triage_agent import run_triage
from app.models.enums import IntentType, WorkflowType
from app.workflows.routing import decide_routing


@pytest.mark.asyncio
async def test_triage_support_route():
    triage = await run_triage(
        user_message="Why was I billed twice and how do I upgrade?",
        active_workflow="triage",
        unresolved_turn_count=0,
        loop_count=0,
    )
    assert triage.intent == IntentType.SUPPORT_CUSTOMER

    decision = decide_routing(triage, current_workflow="triage", human_requested=False)
    assert decision.workflow == WorkflowType.SUPPORT


@pytest.mark.asyncio
async def test_triage_sales_route():
    triage = await run_triage(
        user_message="We are evaluating software for our dental clinic and need pricing",
        active_workflow="support",
        unresolved_turn_count=0,
        loop_count=0,
    )
    assert triage.intent == IntentType.SALES_PROSPECT
