from __future__ import annotations

from dataclasses import dataclass

from app.agents.triage_agent import TriageResult
from app.models.enums import AgentType, IntentType, WorkflowType


@dataclass
class RoutingDecision:
    workflow: WorkflowType
    agent: AgentType
    intent: IntentType
    confidence: float
    reason: str


def decide_routing(
    triage: TriageResult,
    current_workflow: str,
    human_requested: bool,
) -> RoutingDecision:
    if human_requested:
        return RoutingDecision(
            workflow=WorkflowType.HUMAN_ESCALATION,
            agent=AgentType.HUMAN_ESCALATION,
            intent=IntentType.HUMAN_ESCALATION,
            confidence=1.0,
            reason="User requested human escalation.",
        )

    if triage.intent == IntentType.HUMAN_ESCALATION:
        return RoutingDecision(
            workflow=WorkflowType.SUPPORT,
            agent=AgentType.SUPPORT,
            intent=triage.intent,
            confidence=max(triage.confidence, 0.6),
            reason="A human handoff may help, but the user has not explicitly requested one yet.",
        )

    return RoutingDecision(
        workflow=WorkflowType.SUPPORT,
        agent=AgentType.SUPPORT,
        intent=triage.intent,
        confidence=max(triage.confidence, 0.58),
        reason="Practice Desk is limited to support workflows, so the request stays in the support lane unless a human handoff is requested.",
    )
