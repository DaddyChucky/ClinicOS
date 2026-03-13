"""Baseline ClinicOS schema.

Revision ID: 20260313_0001
Revises:
Create Date: 2026-03-13 00:01:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260313_0001"
down_revision = None
branch_labels = None
depends_on = None


INDEX_DEFINITIONS = {
    "users": [
        ("ix_users_id", ["id"], False),
        ("ix_users_email", ["email"], True),
    ],
    "conversations": [
        ("ix_conversations_id", ["id"], False),
    ],
    "messages": [
        ("ix_messages_id", ["id"], False),
        ("ix_messages_conversation_id", ["conversation_id"], False),
    ],
    "agent_runs": [
        ("ix_agent_runs_id", ["id"], False),
        ("ix_agent_runs_conversation_id", ["conversation_id"], False),
    ],
    "escalations": [
        ("ix_escalations_id", ["id"], False),
        ("ix_escalations_conversation_id", ["conversation_id"], False),
    ],
    "prospects": [
        ("ix_prospects_id", ["id"], False),
        ("ix_prospects_conversation_id", ["conversation_id"], False),
        ("ix_prospects_clinic_name", ["clinic_name"], False),
    ],
    "outreach_drafts": [
        ("ix_outreach_drafts_id", ["id"], False),
        ("ix_outreach_drafts_prospect_id", ["prospect_id"], False),
        ("ix_outreach_drafts_conversation_id", ["conversation_id"], False),
    ],
    "campaign_drafts": [
        ("ix_campaign_drafts_id", ["id"], False),
        ("ix_campaign_drafts_conversation_id", ["conversation_id"], False),
    ],
    "review_decisions": [
        ("ix_review_decisions_id", ["id"], False),
        ("ix_review_decisions_entity_type", ["entity_type"], False),
        ("ix_review_decisions_entity_id", ["entity_id"], False),
    ],
    "conversation_controls": [
        ("ix_conversation_controls_id", ["id"], False),
        ("ix_conversation_controls_conversation_id", ["conversation_id"], True),
    ],
    "conversation_profile_overrides": [
        ("ix_conversation_profile_overrides_id", ["id"], False),
        ("ix_conversation_profile_overrides_conversation_id", ["conversation_id"], True),
    ],
    "system_controls": [
        ("ix_system_controls_id", ["id"], False),
    ],
    "conversation_event_logs": [
        ("ix_conversation_event_logs_id", ["id"], False),
        ("ix_conversation_event_logs_conversation_id", ["conversation_id"], False),
    ],
    "conversation_deletions": [
        ("ix_conversation_deletions_id", ["id"], False),
        ("ix_conversation_deletions_conversation_id", ["conversation_id"], True),
    ],
}


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(index["name"] == index_name for index in _inspector().get_indexes(table_name))


def _create_table_if_missing(table_name: str, *columns: sa.Column, **kwargs: object) -> None:
    if _has_table(table_name):
        return
    op.create_table(table_name, *columns, **kwargs)


def _create_indexes() -> None:
    for table_name, definitions in INDEX_DEFINITIONS.items():
        for index_name, columns, unique in definitions:
            if _has_index(table_name, index_name):
                continue
            op.create_index(index_name, table_name, columns, unique=unique)


def _drop_legacy_subscription_plan_column() -> None:
    if not _has_table("conversation_profile_overrides"):
        return

    columns = {column["name"] for column in _inspector().get_columns("conversation_profile_overrides")}
    if "subscription_plan" not in columns:
        return

    with op.batch_alter_table("conversation_profile_overrides", recreate="auto") as batch_op:
        batch_op.drop_column("subscription_plan")


def _drop_indexes() -> None:
    for table_name, definitions in INDEX_DEFINITIONS.items():
        for index_name, _, _ in definitions:
            if _has_index(table_name, index_name):
                op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    _create_table_if_missing(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("active_workflow", sa.String(length=64), nullable=False),
        sa.Column("active_agent", sa.String(length=64), nullable=False),
        sa.Column("loop_count", sa.Integer(), nullable=False),
        sa.Column("unresolved_turn_count", sa.Integer(), nullable=False),
        sa.Column("escalation_recommended", sa.Boolean(), nullable=False),
        sa.Column("human_requested", sa.Boolean(), nullable=False),
        sa.Column("last_issue_fingerprint", sa.String(length=255), nullable=True),
        sa.Column("last_agent_confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("agent_name", sa.String(length=64), nullable=True),
        sa.Column("workflow", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("meta_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "agent_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(length=64), nullable=False),
        sa.Column("workflow", sa.String(length=64), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("handoff_to", sa.String(length=64), nullable=True),
        sa.Column("escalation_recommended", sa.Boolean(), nullable=False),
        sa.Column("tool_trace_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "escalations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by_agent", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "prospects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("clinic_name", sa.String(length=255), nullable=False),
        sa.Column("clinic_type", sa.String(length=64), nullable=False),
        sa.Column("specialty", sa.String(length=128), nullable=True),
        sa.Column("size_estimate", sa.String(length=128), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("existing_lead", sa.Boolean(), nullable=False),
        sa.Column("fit_score", sa.Float(), nullable=True),
        sa.Column("pain_points_json", sa.JSON(), nullable=True),
        sa.Column("research_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "outreach_drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prospect_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(length=64), nullable=False),
        sa.Column("personalization_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["prospects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "campaign_drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("audience", sa.String(length=255), nullable=False),
        sa.Column("channel", sa.String(length=64), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("nurture_sequence_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "review_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reviewer_name", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "conversation_controls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("triage_active", sa.Boolean(), nullable=False),
        sa.Column("assistant_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "conversation_profile_overrides",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("clinic_name", sa.String(length=255), nullable=True),
        sa.Column("practice_type", sa.String(length=128), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("locations", sa.Integer(), nullable=True),
        sa.Column("providers", sa.Integer(), nullable=True),
        sa.Column("front_desk_staff_count", sa.Integer(), nullable=True),
        sa.Column("pms_software", sa.String(length=255), nullable=True),
        sa.Column("insurance_billing_status", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "system_controls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("global_agent_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "conversation_event_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("meta_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table_if_missing(
        "conversation_deletions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("deleted_by", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("snapshot_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    _drop_legacy_subscription_plan_column()
    _create_indexes()


def downgrade() -> None:
    _drop_indexes()

    for table_name in [
        "conversation_deletions",
        "conversation_event_logs",
        "system_controls",
        "conversation_profile_overrides",
        "conversation_controls",
        "review_decisions",
        "campaign_drafts",
        "outreach_drafts",
        "prospects",
        "escalations",
        "agent_runs",
        "messages",
        "conversations",
        "users",
    ]:
        if _has_table(table_name):
            op.drop_table(table_name)
