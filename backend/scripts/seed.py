from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import init_db, SessionLocal
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.draft_repository import DraftRepository
from app.repositories.prospect_repository import ProspectRepository


def main() -> None:
    init_db()
    db = SessionLocal()

    conversation_repo = ConversationRepository(db)
    prospect_repo = ProspectRepository(db)
    draft_repo = DraftRepository(db)

    user = conversation_repo.get_or_create_user(
        email="seed-user@clinicos.app",
        name="Seed User",
        role="internal",
    )
    conversation = conversation_repo.create_conversation(user_id=user.id, title="Seed Demo Conversation")

    conversation_repo.add_message(
        conversation_id=conversation.id,
        role="user",
        content="Why was I billed twice and how do I upgrade?",
    )
    conversation_repo.add_message(
        conversation_id=conversation.id,
        role="assistant",
        content="I can help with billing and upgrade guidance. If you need account-level action, I can escalate.",
        agent_name="support_agent",
        workflow="support",
        confidence=0.86,
    )

    prospect = prospect_repo.create_or_update(
        clinic_name="Sunrise Family Dental",
        clinic_type="dental",
        conversation_id=conversation.id,
        specialty="family dentistry",
        size_estimate="4-8 providers",
        location="Austin, TX",
        existing_lead=True,
        fit_score=84.0,
        pain_points=["manual recall reminders", "insurance verification delays"],
        research_summary="Strong dental ICP fit with admin workflow bottlenecks.",
    )

    draft_repo.create_outreach_draft(
        prospect_id=prospect.id,
        conversation_id=conversation.id,
        subject="Workflow idea for Sunrise Family Dental",
        body="Hi Sunrise team, sharing a short workflow map to reduce recall and billing follow-up load.",
        tone="consultative",
        personalization_notes="High ICP fit, expansion signal detected",
    )

    draft_repo.create_campaign_draft(
        conversation_id=conversation.id,
        title="No-Show Reduction for Front Desk Teams",
        audience="office managers and front desk leads",
        channel="email",
        brief="Campaign focused on reminder workflows and schedule stability.",
        nurture_sequence=[
            {"step": 1, "subject": "Quick win for no-show reduction", "goal": "Awareness"},
            {"step": 2, "subject": "Front desk checklist template", "goal": "Education"},
            {"step": 3, "subject": "Book workflow audit", "goal": "Conversion"},
        ],
    )

    db.close()
    print("Seed complete.")


if __name__ == "__main__":
    main()
