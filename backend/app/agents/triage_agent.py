from __future__ import annotations

from dataclasses import dataclass

from app.agents.common import load_prompt, try_sdk_json
from app.models.enums import AgentType, IntentType, WorkflowType
from app.services.telemetry_service import log_agent_event
from app.tools.shared_tools import (
    detect_frustration,
    detect_frustration_tool,
    identify_user_role,
    identify_user_role_tool,
)


@dataclass
class TriageResult:
    intent: IntentType
    inferred_role: str
    next_workflow: WorkflowType
    next_agent: AgentType
    confidence: float
    escalation_recommended: bool
    reason: str
    support_score: int
    sales_score: int
    marketing_score: int
    detected_tracks: list[str]
    mixed_intent: bool


def _keyword_score(text: str, keywords: list[str]) -> int:
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword in lower)


def _clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, round(value, 2)))


def _to_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in {"true", "yes", "1"}:
            return True
        if value.lower() in {"false", "no", "0"}:
            return False
    return default


def _to_intent(value: object, default: IntentType) -> IntentType:
    if isinstance(value, IntentType):
        return value
    if not isinstance(value, str):
        return default
    normalized = value.strip().lower()
    mapping = {
        "support_customer": IntentType.SUPPORT_CUSTOMER,
        "support": IntentType.SUPPORT_CUSTOMER,
        "sales_prospect": IntentType.SALES_PROSPECT,
        "sales": IntentType.SALES_PROSPECT,
        "marketing_internal": IntentType.MARKETING_INTERNAL,
        "marketing": IntentType.MARKETING_INTERNAL,
        "human_escalation": IntentType.HUMAN_ESCALATION,
        "human": IntentType.HUMAN_ESCALATION,
        "unknown": IntentType.UNKNOWN,
    }
    return mapping.get(normalized, default)


def _workflow_and_agent_for_intent(intent: IntentType, active_workflow: str) -> tuple[WorkflowType, AgentType]:
    if intent == IntentType.SUPPORT_CUSTOMER:
        return WorkflowType.SUPPORT, AgentType.SUPPORT
    if intent == IntentType.SALES_PROSPECT:
        return WorkflowType.SALES, AgentType.SALES_RESEARCH
    if intent == IntentType.MARKETING_INTERNAL:
        return WorkflowType.MARKETING, AgentType.MARKETING_STRATEGIST
    if intent == IntentType.HUMAN_ESCALATION:
        return WorkflowType.HUMAN_ESCALATION, AgentType.HUMAN_ESCALATION

    if active_workflow in {WorkflowType.SUPPORT, WorkflowType.SALES, WorkflowType.MARKETING}:
        workflow = WorkflowType(active_workflow)
        if workflow == WorkflowType.SUPPORT:
            return workflow, AgentType.SUPPORT
        if workflow == WorkflowType.SALES:
            return workflow, AgentType.SALES_RESEARCH
        return workflow, AgentType.MARKETING_STRATEGIST

    return WorkflowType.SUPPORT, AgentType.SUPPORT


def _extract_tracks(raw_tracks: object, support_score: int, sales_score: int, marketing_score: int) -> list[str]:
    if isinstance(raw_tracks, list):
        valid = [str(item).strip().lower() for item in raw_tracks if str(item).strip().lower() in {"support", "sales", "marketing"}]
        if valid:
            return list(dict.fromkeys(valid))

    detected_tracks: list[str] = []
    if support_score > 0:
        detected_tracks.append("support")
    if sales_score > 0:
        detected_tracks.append("sales")
    if marketing_score > 0:
        detected_tracks.append("marketing")
    return detected_tracks


async def run_triage(
    user_message: str,
    active_workflow: str,
    unresolved_turn_count: int,
    loop_count: int,
) -> TriageResult:
    lower = user_message.lower()

    support_score = _keyword_score(
        lower,
        [
            "billing",
            "invoice",
            "upgrade",
            "help",
            "error",
            "failed",
            "sync",
            "double charged",
            "login",
            "claim",
            "faq",
        ],
    )
    sales_score = _keyword_score(
        lower,
        [
            "evaluating",
            "not a customer",
            "demo",
            "pricing",
            "quote",
            "prospect",
            "outreach",
            "lead",
            "clinic",
            "buy",
            "considering",
        ],
    )
    marketing_score = _keyword_score(
        lower,
        [
            "marketing",
            "campaign",
            "nurture",
            "persona",
            "content",
            "newsletter",
            "webinar",
            "funnel",
        ],
    )

    frustration = detect_frustration(user_message)
    inferred_role = identify_user_role(user_message)

    if "human" in lower or "person" in lower or frustration["frustrated"]:
        intent = IntentType.HUMAN_ESCALATION
    elif marketing_score > max(sales_score, support_score):
        intent = IntentType.MARKETING_INTERNAL
    elif sales_score > max(marketing_score, support_score):
        intent = IntentType.SALES_PROSPECT
    elif support_score > 0:
        intent = IntentType.SUPPORT_CUSTOMER
    else:
        intent = IntentType.UNKNOWN

    detected_tracks = _extract_tracks(None, support_score, sales_score, marketing_score)
    mixed_intent = len(detected_tracks) >= 2

    confidence = 0.75 if intent != IntentType.UNKNOWN else 0.55
    if frustration["frustrated"]:
        confidence -= 0.1

    escalation_recommended = (
        intent == IntentType.HUMAN_ESCALATION
        or unresolved_turn_count >= 2
        or loop_count >= 2
        or frustration["frustration_score"] >= 0.55
    )
    reason = f"Intent={intent}; support={support_score}, sales={sales_score}, marketing={marketing_score}."

    workflow, agent = _workflow_and_agent_for_intent(intent, active_workflow)
    mode = "fallback"

    prompt = load_prompt("triage.md")
    json_payload = await try_sdk_json(
        agent_name="Triage Agent",
        instructions=(
            f"{prompt}\n\n"
            "Return valid JSON only with keys: "
            "intent, inferred_role, confidence, escalation_recommended, reason, detected_tracks, mixed_intent."
        ),
        input_text=(
            "Message to triage:\n"
            f"{user_message}\n\n"
            f"Current workflow: {active_workflow}\n"
            f"Unresolved turns: {unresolved_turn_count}\n"
            f"Loop count: {loop_count}"
        ),
        tools=[identify_user_role_tool, detect_frustration_tool],
    )

    if json_payload:
        mode = "live_ai"
        intent = _to_intent(json_payload.get("intent"), intent)
        workflow, agent = _workflow_and_agent_for_intent(intent, active_workflow)
        inferred_role = str(json_payload.get("inferred_role") or inferred_role)
        reason = str(json_payload.get("reason") or reason)
        detected_tracks = _extract_tracks(json_payload.get("detected_tracks"), support_score, sales_score, marketing_score)
        mixed_intent = _to_bool(json_payload.get("mixed_intent"), len(detected_tracks) >= 2)

        try:
            confidence = _clamp_confidence(float(json_payload.get("confidence", confidence)))
        except (TypeError, ValueError):
            confidence = _clamp_confidence(confidence)
        escalation_recommended = _to_bool(json_payload.get("escalation_recommended"), escalation_recommended)
    else:
        confidence = _clamp_confidence(confidence)

    log_agent_event(
        agent=str(agent),
        workflow=str(workflow),
        mode=mode,
        detail={
            "intent": str(intent),
            "confidence": confidence,
            "mixed_intent": mixed_intent,
            "detected_tracks": detected_tracks,
        },
    )

    return TriageResult(
        intent=intent,
        inferred_role=inferred_role,
        next_workflow=workflow,
        next_agent=agent,
        confidence=confidence,
        escalation_recommended=escalation_recommended,
        reason=reason,
        support_score=support_score,
        sales_score=sales_score,
        marketing_score=marketing_score,
        detected_tracks=detected_tracks,
        mixed_intent=mixed_intent,
    )

