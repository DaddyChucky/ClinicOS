from enum import StrEnum


class IntentType(StrEnum):
    SUPPORT_CUSTOMER = "support_customer"
    SALES_PROSPECT = "sales_prospect"
    MARKETING_INTERNAL = "marketing_internal"
    HUMAN_ESCALATION = "human_escalation"
    UNKNOWN = "unknown"


class WorkflowType(StrEnum):
    TRIAGE = "triage"
    SUPPORT = "support"
    SALES = "sales"
    MARKETING = "marketing"
    HUMAN_ESCALATION = "human_escalation"
    UNKNOWN = "unknown"


class AgentType(StrEnum):
    TRIAGE = "triage_agent"
    SUPPORT = "support_agent"
    SALES_RESEARCH = "sales_research_agent"
    SALES_OUTREACH = "sales_outreach_agent"
    MARKETING_STRATEGIST = "marketing_strategist_agent"
    MARKETING_CONTENT = "marketing_content_agent"
    HUMAN_ESCALATION = "human_escalation"


class ConversationStatus(StrEnum):
    OPEN = "open"
    ESCALATED = "escalated"
    CLOSED = "closed"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class EscalationStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class DraftStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewEntityType(StrEnum):
    OUTREACH = "outreach"
    CAMPAIGN = "campaign"


class ReviewDecisionType(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
