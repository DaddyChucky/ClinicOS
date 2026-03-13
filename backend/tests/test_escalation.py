from __future__ import annotations

import pytest

from app.api.chat import start_chat
from app.api.support import talk_to_human
from app.models.schemas import ChatStartRequest
from app.workflows.escalation import should_trigger_escalation


def test_escalation_triggers_on_low_confidence():
    assert should_trigger_escalation(
        human_requested=False,
        unresolved_turn_count=1,
        loop_count=0,
        confidence=0.42,
        frustration_score=0.2,
        agent_requested=False,
    )


@pytest.mark.asyncio
async def test_support_endpoint_talk_to_human_creates_escalation(db_session):
    conversation = await start_chat(
        ChatStartRequest(
            user_name="Tester",
            user_email="tester@clinicos.app",
            opening_message=None,
        ),
        db_session,
    )

    escalation = talk_to_human(conversation.id, db_session)
    assert escalation.conversation_id == conversation.id
    assert escalation.status == "open"
