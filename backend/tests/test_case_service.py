from __future__ import annotations

from app.database import SessionLocal
from app.models.enums import MessageRole
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.draft_repository import DraftRepository
from app.repositories.prospect_repository import ProspectRepository
from app.services.case_service import CaseService


def test_case_service_builds_snapshot_with_tasks():
    db_session = SessionLocal()
    conversation_repo = ConversationRepository(db_session)
    prospect_repo = ProspectRepository(db_session)
    draft_repo = DraftRepository(db_session)

    user = conversation_repo.get_or_create_user("ops@clinicos.app", "Ops Lead")
    conversation = conversation_repo.create_conversation(user.id, "Mixed Clinic Request")

    conversation_repo.add_message(
        conversation.id,
        MessageRole.USER,
        "We are opening a second location and our claims sync in Dentrix is delayed.",
    )
    conversation_repo.add_run_log(
        conversation_id=conversation.id,
        agent_name="support_agent",
        workflow="support",
        input_text="Need claims help",
        output_text="Investigating claims sync and requesting batch log sample.",
        confidence=0.74,
        handoff_to=None,
        escalation_recommended=False,
        tool_trace_json={"tools": []},
    )

    prospect = prospect_repo.create_or_update(
        clinic_name="Sunrise Family Dental",
        clinic_type="dental",
        conversation_id=conversation.id,
        specialty="general dentistry",
        size_estimate="4-8 providers",
        location="Austin, TX",
        existing_lead=False,
        fit_score=82,
        pain_points=["claims delay", "front desk overload"],
        research_summary="Strong fit with multi-location growth signal.",
    )
    draft_repo.create_outreach_draft(
        prospect_id=prospect.id,
        conversation_id=conversation.id,
        subject="Scaling support for your second location",
        body="Draft outreach body",
        tone="consultative",
        personalization_notes="Mention claims automation workflow",
    )

    try:
        context = conversation_repo.get_conversation_with_context(conversation.id)
        assert context is not None

        snapshot = CaseService().build_case_snapshot(context)
        tracks = {task.track for task in snapshot.tasks}

        assert snapshot.case_id.startswith("CASE-")
        assert "support" in tracks
        assert "sales" in tracks
        assert snapshot.clinic_memory.locations == 2
        assert snapshot.clinic_memory.pms_software == "Dentrix"
    finally:
        db_session.close()
