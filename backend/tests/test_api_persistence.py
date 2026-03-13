from __future__ import annotations

import pytest

from app.api.chat import (
    delete_conversation,
    get_chat,
    list_conversations,
    list_deleted_thread_archive,
    send_message,
    start_chat,
    update_practice_profile,
)
from app.api.marketing import generate_marketing, list_drafts as list_marketing_drafts
from app.api.sales import sales_research, sales_research_history
from app.api.support import (
    get_support_status,
    list_support_queue,
    reply_to_chat,
    take_over_chat,
    talk_to_human,
)
from app.models.schemas import (
    ChatMessageRequest,
    ChatStartRequest,
    HumanSupportReplyRequest,
    MarketingGenerateRequest,
    PracticeProfileUpdateRequest,
    SalesResearchRequest,
)


async def _start_chat(db_session):
    return await start_chat(
        ChatStartRequest(
            user_name="Practice Manager",
            user_email="manager@clinicos.app",
            opening_message=None,
        ),
        db_session,
    )


@pytest.mark.asyncio
async def test_chat_message_profile_and_archive_persistence(db_session):
    conversation = await _start_chat(db_session)

    message = await send_message(
        ChatMessageRequest(
            conversation_id=conversation.id,
            message="Our Dentrix claims queue is stuck in Austin and we have four providers.",
        ),
        db_session,
    )
    assert message.conversation_id == conversation.id
    assert message.assistant_message

    profile = await update_practice_profile(
        conversation.id,
        PracticeProfileUpdateRequest(
            clinic_name="Downtown Dental Group",
            practice_type="General Dentistry",
            location="Austin, TX",
            providers=4,
            front_desk_staff_count=6,
            pms_software="Dentrix",
            insurance_billing_status="Claims queue stalled after nightly sync",
        ),
        db_session,
    )
    assert profile.clinic_memory.clinic_name == "Downtown Dental Group"
    assert profile.clinic_memory.pms_software == "Dentrix"
    assert profile.clinic_memory.providers == 4

    thread = await get_chat(conversation.id, db_session)
    assert len(thread.messages) == 2
    assert thread.messages[0].role == "user"
    assert thread.messages[1].role == "assistant"

    deletion = await delete_conversation(conversation.id, deleted_by="user", db=db_session)
    assert deletion.conversation_id == conversation.id
    assert deletion.deleted_by == "user"

    active_threads = await list_conversations(user_email="manager@clinicos.app", limit=25, db=db_session)
    assert all(item.id != conversation.id for item in active_threads)

    archived_threads = await list_deleted_thread_archive(limit=50, db=db_session)
    archived = next(item for item in archived_threads if item.conversation_id == conversation.id)
    assert archived.snapshot_json["case_snapshot"]["clinic_memory"]["clinic_name"] == "Downtown Dental Group"
    assert len(archived.snapshot_json["messages"]) == 2


@pytest.mark.asyncio
async def test_human_handoff_queue_and_live_reply_persistence(db_session):
    conversation = await _start_chat(db_session)

    escalation = talk_to_human(conversation.id, db_session)
    assert escalation.status == "open"
    assert escalation.queue_position == 1

    queue = list_support_queue(db_session)
    assert queue[0].conversation_id == conversation.id
    assert queue[0].handoff_stage == "queued"

    takeover = take_over_chat(conversation.id, db_session)
    assert takeover.handoff_stage == "reviewing"

    reply = reply_to_chat(
        conversation.id,
        HumanSupportReplyRequest(message="I'm reviewing this with billing now.", responder_name="Human Support"),
        db_session,
    )
    assert reply.meta_json["sender_type"] == "human"

    status = get_support_status(conversation.id, db_session)
    assert status.handoff_stage == "live_chat"

    follow_up = await send_message(
        ChatMessageRequest(
            conversation_id=conversation.id,
            message="Thanks, I will wait here for the update.",
        ),
        db_session,
    )
    assert follow_up.assistant_message == ""
    assert follow_up.active_workflow == "human_escalation"

    thread = await get_chat(conversation.id, db_session)
    assert any(message.role == "system" for message in thread.messages)
    assert any((message.meta_json or {}).get("sender_type") == "human" for message in thread.messages)


@pytest.mark.asyncio
async def test_sales_and_marketing_history_persistence(db_session):
    sales = await sales_research(
        SalesResearchRequest(
            clinic_name="Sunrise Family Dental",
            location="Austin, TX",
        ),
        db_session,
    )
    assert sales.outreach_draft.conversation_id is None

    sales_history = sales_research_history(db_session)
    assert len(sales_history) == 1
    assert sales_history[0].clinic_name == "Sunrise Family Dental"

    marketing = await generate_marketing(
        MarketingGenerateRequest(
            audience="Overdue hygiene patients with no visit in 9+ months",
            objective="Hygiene Recall Reactivation",
            segment_notes="manual reminder backlog, open chair time next month",
        ),
        db_session,
    )
    assert marketing.conversation_id is None
    assert marketing.title

    marketing_history = list_marketing_drafts(db_session)
    assert len(marketing_history) == 1
    assert marketing_history[0].title == marketing.title
