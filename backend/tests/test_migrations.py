from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

if importlib.util.find_spec("alembic.command") is None:
    pytest.skip("Alembic is not installed in the current environment.", allow_module_level=True)

from alembic import command
from alembic.config import Config

from app.database import Base
from app.models import db_models
from app.models.enums import MessageRole
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.draft_repository import DraftRepository
from app.repositories.escalation_repository import EscalationRepository
from app.repositories.prospect_repository import ProspectRepository
from scripts.port_sqlite_to_database import TABLE_COPY_ORDER, copy_sqlite_to_database

ROOT = Path(__file__).resolve().parents[1]


def _alembic_config(database_url: str) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_alembic_upgrade_creates_current_schema(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'migrated.db'}"
    command.upgrade(_alembic_config(database_url), "head")

    inspector = sa.inspect(sa.create_engine(database_url, future=True))
    table_names = set(inspector.get_table_names())

    assert set(TABLE_COPY_ORDER).issubset(table_names)
    assert "alembic_version" in table_names


def test_sqlite_copy_script_preserves_data_into_migrated_target(tmp_path):
    source_url = f"sqlite:///{tmp_path / 'source.db'}"
    target_url = f"sqlite:///{tmp_path / 'target.db'}"

    source_engine = sa.create_engine(source_url, future=True)
    Base.metadata.create_all(bind=source_engine)
    SourceSession = sessionmaker(bind=source_engine, autoflush=False, autocommit=False, expire_on_commit=False)

    source_session = SourceSession()
    try:
        conversation_repo = ConversationRepository(source_session)
        prospect_repo = ProspectRepository(source_session)
        draft_repo = DraftRepository(source_session)
        escalation_repo = EscalationRepository(source_session)

        user = conversation_repo.get_or_create_user("ops@clinicos.app", "Ops Lead")
        conversation = conversation_repo.create_conversation(user.id, "Billing issue with handoff")
        conversation_repo.add_message(
            conversation.id,
            MessageRole.USER,
            "Dentrix claims stopped posting and we need a human.",
        )
        conversation_repo.add_message(
            conversation.id,
            MessageRole.SYSTEM,
            "ClinicOS AI Agent has disconnected from this chat. A human support specialist will assist you shortly.",
            agent_name="ClinicOS System",
            workflow="human_escalation",
            meta_json={"sender_type": "system", "event": "human_handoff_requested", "queue_position": 1},
        )
        conversation_repo.add_run_log(
            conversation_id=conversation.id,
            agent_name="support_agent",
            workflow="support",
            input_text="Dentrix claims stopped posting",
            output_text="I need a human specialist to review this billing issue.",
            confidence=0.48,
            handoff_to=None,
            escalation_recommended=True,
            tool_trace_json={"tools": []},
        )
        conversation_repo.add_event_log(
            conversation_id=conversation.id,
            stage="ClinicOS AI Agent Handoff",
            detail="The chat moved into the human review queue.",
            status="offline",
            meta_json={"queue_position": 1},
        )
        escalation_repo.create(
            conversation_id=conversation.id,
            summary="User requested human support for a Dentrix billing issue.",
            reason="User requested human support",
            created_by_agent="ClinicOS AI Triage Agent",
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
            pain_points=["claims delay", "manual reminders"],
            research_summary="Strong fit with clear billing workflow pain.",
        )
        draft_repo.create_outreach_draft(
            prospect_id=prospect.id,
            conversation_id=conversation.id,
            subject="Reducing billing delays at Sunrise Family Dental",
            body="Draft outreach body",
            tone="consultative",
            personalization_notes="Mention Dentrix claims workflow",
        )
        draft_repo.create_campaign_draft(
            conversation_id=conversation.id,
            title="Recall Reactivation Plan",
            audience="Overdue hygiene patients",
            channel="email",
            brief="Campaign focused on reminder recovery and scheduling consistency.",
            nurture_sequence=[{"step": 1, "subject": "Quick recall win", "goal": "Awareness"}],
        )
        source_session.add(db_models.ConversationControl(conversation_id=conversation.id, triage_active=True, assistant_active=True))
        source_session.add(
            db_models.ConversationProfileOverride(
                conversation_id=conversation.id,
                clinic_name="Sunrise Family Dental",
                practice_type="General Dentistry",
                location="Austin, TX",
                providers=4,
                front_desk_staff_count=6,
                pms_software="Dentrix",
                insurance_billing_status="Claims queue stalled",
            )
        )
        source_session.add(
            db_models.SystemControl(global_agent_enabled=True)
        )
        source_session.add(
            db_models.ConversationDeletion(
                conversation_id=conversation.id,
                title=conversation.title,
                deleted_by="admin",
                summary="Archived for audit review.",
                snapshot_json={"messages": 2},
            )
        )
        source_session.commit()
    finally:
        source_session.close()

    command.upgrade(_alembic_config(target_url), "head")

    copied_rows = copy_sqlite_to_database(source_url=source_url, target_url=target_url)
    assert copied_rows["conversations"] == 1
    assert copied_rows["messages"] == 2
    assert copied_rows["escalations"] == 1
    assert copied_rows["conversation_deletions"] == 1

    target_engine = sa.create_engine(target_url, future=True)
    with target_engine.connect() as connection:
        for table_name, expected_count in {
            "users": 1,
            "conversations": 1,
            "messages": 2,
            "agent_runs": 1,
            "escalations": 1,
            "prospects": 1,
            "outreach_drafts": 1,
            "campaign_drafts": 1,
            "conversation_controls": 1,
            "conversation_profile_overrides": 1,
            "system_controls": 1,
            "conversation_event_logs": 1,
            "conversation_deletions": 1,
        }.items():
            table = sa.Table(table_name, sa.MetaData(), autoload_with=target_engine)
            assert connection.execute(select(func.count()).select_from(table)).scalar_one() == expected_count

        conversations = sa.Table("conversations", sa.MetaData(), autoload_with=target_engine)
        stored_conversation = connection.execute(select(conversations.c.title, conversations.c.active_workflow)).one()
        assert stored_conversation.title == "Billing issue with handoff"
        assert stored_conversation.active_workflow == "triage"
