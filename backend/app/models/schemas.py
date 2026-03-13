from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    AgentType,
    DraftStatus,
    EscalationStatus,
    IntentType,
    MessageRole,
    ReviewDecisionType,
    ReviewEntityType,
    WorkflowType,
)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class MessageRead(BaseModel):
    id: int
    role: MessageRole
    content: str
    agent_name: str | None = None
    workflow: str | None = None
    confidence: float | None = None
    meta_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatStartRequest(BaseModel):
    user_name: str = "Practice Manager"
    user_email: str = "manager@clinicos.app"
    opening_message: str | None = None


class HandoffInfo(BaseModel):
    from_agent: str
    to_agent: str
    reason: str


class DraftRef(BaseModel):
    id: int
    type: ReviewEntityType
    status: DraftStatus


class ChatMessageRequest(BaseModel):
    conversation_id: int
    message: str


class ConversationControlRead(BaseModel):
    active_chat_enabled: bool
    global_agent_enabled: bool
    workspace_available: bool
    admin_message: str | None = None
    updated_at: datetime | None = None
    global_updated_at: datetime | None = None


class ConversationControlUpdateRequest(BaseModel):
    active_chat_enabled: bool | None = None
    global_agent_enabled: bool | None = None


class PracticeProfileUpdateRequest(BaseModel):
    clinic_name: str | None = None
    practice_type: str | None = None
    location: str | None = None
    providers: int | None = None
    front_desk_staff_count: int | None = None
    pms_software: str | None = None
    insurance_billing_status: str | None = None


class ChatMessageResponse(BaseModel):
    conversation_id: int
    assistant_message: str
    active_workflow: WorkflowType
    active_agent: AgentType | str
    intent: IntentType
    confidence: float
    handoff: HandoffInfo | None = None
    escalation_recommended: bool = False
    human_requested: bool = False
    escalation_id: int | None = None
    escalation_summary: str | None = None
    review_required: bool = False
    drafts_created: list[DraftRef] = Field(default_factory=list)
    loop_count: int
    unresolved_turn_count: int


class ConversationRead(BaseModel):
    id: int
    user_id: int | None
    title: str | None
    status: str
    active_workflow: str
    active_agent: str
    loop_count: int
    unresolved_turn_count: int
    escalation_recommended: bool
    human_requested: bool
    messages: list[MessageRead]

    model_config = {"from_attributes": True}


class ConversationSummaryRead(BaseModel):
    id: int
    title: str | None
    updated_at: datetime
    last_message_preview: str | None = None

    model_config = {"from_attributes": True}


class EscalationCreateRequest(BaseModel):
    conversation_id: int
    reason: str
    summary: str | None = None
    created_by_agent: str | None = None


class EscalationRead(BaseModel):
    id: int
    conversation_id: int
    summary: str
    reason: str
    status: EscalationStatus | str
    queue_position: int | None = None
    created_by_agent: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HumanSupportReplyRequest(BaseModel):
    message: str = Field(min_length=1)
    responder_name: str = "Human Support"


class HumanSupportQueueItemRead(BaseModel):
    escalation_id: int
    conversation_id: int
    chat_title: str
    category: str
    status: EscalationStatus | str
    handoff_stage: str
    queue_position: int | None = None
    summary: str
    summary_points: list[str] = Field(default_factory=list)
    latest_message_preview: str | None = None
    clinic_name: str | None = None
    practice_type: str | None = None
    requested_at: datetime
    updated_at: datetime


class SalesResearchRequest(BaseModel):
    conversation_id: int | None = None
    clinic_name: str
    location: str | None = None


class ProspectRead(BaseModel):
    id: int
    conversation_id: int | None = None
    clinic_name: str
    clinic_type: str
    specialty: str | None = None
    size_estimate: str | None = None
    location: str | None = None
    existing_lead: bool
    fit_score: float | None = None
    pain_points_json: list[str] | None = None
    research_summary: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OutreachDraftRead(BaseModel):
    id: int
    prospect_id: int
    conversation_id: int | None = None
    subject: str
    body: str
    tone: str
    personalization_notes: str | None = None
    status: DraftStatus | str
    review_required: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SalesResearchResponse(BaseModel):
    prospect: ProspectRead
    fit_score: float
    fit_reasons: list[str]
    summary: str
    outreach_draft: OutreachDraftRead


class SalesResearchHistoryItemRead(BaseModel):
    id: int
    clinic_name: str
    clinic_type: str
    specialty: str | None = None
    size_estimate: str | None = None
    location: str | None = None
    existing_lead: bool
    fit_score: float | None = None
    pain_points_json: list[str] | None = None
    research_summary: str | None = None
    outreach_subject: str
    outreach_body: str
    personalization_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class MarketingGenerateRequest(BaseModel):
    conversation_id: int | None = None
    audience: str
    objective: str
    segment_notes: str | None = None


class CampaignDraftRead(BaseModel):
    id: int
    conversation_id: int | None = None
    title: str
    audience: str
    channel: str
    brief: str
    nurture_sequence_json: list[dict] | None = None
    status: DraftStatus | str
    review_required: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewActionRequest(BaseModel):
    reviewer_name: str = "Reviewer"
    notes: str | None = None


class ReviewDecisionRead(BaseModel):
    id: int
    entity_type: ReviewEntityType | str
    entity_id: int
    decision: ReviewDecisionType | str
    reviewer_name: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewQueueItem(BaseModel):
    entity_type: ReviewEntityType
    draft_id: int
    conversation_id: int | None
    title: str
    status: DraftStatus
    review_required: bool
    created_at: datetime


class DeleteResultRead(BaseModel):
    id: int
    deleted: bool


class ClinicMemoryRead(BaseModel):
    clinic_name: str | None = None
    practice_type: str | None = None
    location: str | None = None
    locations: int | None = None
    providers: int | None = None
    front_desk_staff_count: int | None = None
    pms_software: str | None = None
    insurance_billing_status: str | None = None
    open_support_issues: list[str] = Field(default_factory=list)
    growth_signals: list[str] = Field(default_factory=list)
    prior_sales_interactions: list[str] = Field(default_factory=list)
    marketing_engagement_history: list[str] = Field(default_factory=list)
    active_tasks: list[str] = Field(default_factory=list)
    unresolved_blockers: list[str] = Field(default_factory=list)
    response_preferences: list[str] = Field(default_factory=list)
    known_profile_fields: list[str] = Field(default_factory=list)
    missing_profile_fields: list[str] = Field(default_factory=list)
    profile_completion_score: int = 0


class CaseTaskRead(BaseModel):
    task_id: str
    track: str
    agent: str
    status: str
    summary: str
    needs_human_review: bool = False
    blocked_reason: str | None = None
    updated_at: datetime


class CaseTimelineEventRead(BaseModel):
    event_id: str
    stage: str
    detail: str
    status: str
    timestamp: datetime


class CaseSnapshotRead(BaseModel):
    conversation_id: int
    case_id: str
    title: str
    status: str
    intent_mix: list[str] = Field(default_factory=list)
    recommended_next_actions: list[str] = Field(default_factory=list)
    tasks: list[CaseTaskRead] = Field(default_factory=list)
    timeline: list[CaseTimelineEventRead] = Field(default_factory=list)
    clinic_memory: ClinicMemoryRead
    controls: ConversationControlRead | None = None


class ConversationDeletionRead(BaseModel):
    id: int
    conversation_id: int
    title: str | None = None
    deleted_by: str
    summary: str
    snapshot_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    app: str


class OpenAIHealthResponse(BaseModel):
    status: str
    sdk_available: bool
    api_key_loaded: bool
    model: str
    live_mode_ready: bool
    test_call_success: bool
    runtime_mode: str
    detail: str | None = None
