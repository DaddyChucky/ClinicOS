from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.common import load_prompt, try_sdk_json
from app.services.telemetry_service import log_agent_event
from app.tools.shared_tools import detect_frustration
from app.tools.support_tools import (
    lookup_billing_faq,
    lookup_billing_faq_tool,
    lookup_upgrade_options,
    lookup_upgrade_options_tool,
    search_help_center,
    search_help_center_tool,
)


@dataclass
class SupportResult:
    answer: str
    confidence: float
    resolved: bool
    escalation_recommended: bool
    escalation_reason: str | None
    handoff_to_sales: bool
    operational_summary: str = ""
    assumptions: list[str] = field(default_factory=list)
    unresolved_info: list[str] = field(default_factory=list)
    memory_updates: dict[str, str] = field(default_factory=dict)


ACCOUNT_SPECIFIC_PATTERNS = [
    "refund",
    "change card",
    "update payment method",
    "close account",
    "transfer data",
    "patient record correction",
]


def _is_prospect_signal(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in [
            "not a customer",
            "evaluating",
            "looking for software",
            "considering switching",
            "demo",
        ]
    )


def _is_growth_or_marketing_request(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in [
            "marketing",
            "campaign",
            "outreach",
            "prospect",
            "lead gen",
            "lead generation",
            "sales",
            "referral partners",
            "reactivation plan",
            "nurture sequence",
            "promote",
        ]
    )


def _to_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in {"true", "yes", "1"}:
            return True
        if value.lower() in {"false", "no", "0"}:
            return False
    return default


def _to_float(value: object, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(0.0, min(1.0, round(parsed, 2)))


def _to_str_list(value: object, default: list[str]) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or default
    return default


def _to_memory_updates(value: object, default: dict[str, str]) -> dict[str, str]:
    if isinstance(value, dict):
        payload: dict[str, str] = {}
        for key, item in value.items():
            if not str(key).strip():
                continue
            payload[str(key)] = str(item)
        return payload or default
    return default


async def run_support(
    user_message: str,
    unresolved_turn_count: int,
    clinic_memory: dict | None = None,
) -> SupportResult:
    lower = user_message.lower()
    clinic_memory = clinic_memory or {}

    kb = search_help_center(user_message)["results"]
    billing = lookup_billing_faq(user_message)["results"]
    upgrades = lookup_upgrade_options(user_message)["results"]

    snippets: list[str] = []
    if billing:
        snippets.append(f"Billing: {billing[0]['answer']}")
    if upgrades:
        snippets.append(f"Upgrade: {upgrades[0]['summary']}")
    if kb:
        snippets.append(f"Help center: {kb[0]['summary']}")

    frustration = detect_frustration(user_message)
    account_specific = any(pattern in lower for pattern in ACCOUNT_SPECIFIC_PATTERNS)
    handoff_to_sales = _is_prospect_signal(user_message)

    if handoff_to_sales or _is_growth_or_marketing_request(user_message):
        result = SupportResult(
            answer=(
                "Practice Desk is focused on existing-customer support, including software questions, upgrade guidance, billing FAQs, "
                "and escalation routing. For clinic prospecting, outreach, or marketing planning, please use the Sales & Outreach or "
                "Marketing tools in Operations Console."
            ),
            confidence=0.92,
            resolved=True,
            escalation_recommended=False,
            escalation_reason=None,
            handoff_to_sales=False,
            operational_summary="Detected a non-support request in Practice Desk and redirected the user to Operations Console specialist tools.",
            assumptions=["Practice Desk should stay limited to support workflows for existing customers."],
            unresolved_info=[],
            memory_updates={},
        )
        log_agent_event(
            agent="support_agent",
            workflow="support",
            mode="fallback",
            detail={"redirected_to_operations_console": True, "reason": "non_support_request"},
        )
        return result

    if snippets:
        answer = "\n\n".join(snippets)
        if clinic_memory.get("pms_software"):
            answer += f"\n\nUsing your current PMS context ({clinic_memory['pms_software']}) for next-step guidance."
        answer += "\n\nIf you want, I can also outline exact click-path steps for your front desk workflow."
        confidence = 0.84
        resolved = True
    else:
        answer = (
            "I don’t have enough context to resolve this confidently from our standard knowledge base. "
            "Please share your exact workflow step and screen details, or ask for human support if this needs account-level help."
        )
        confidence = 0.46
        resolved = False

    escalation_reason = None
    escalation_recommended = False
    if account_specific:
        escalation_recommended = True
        escalation_reason = "Account-specific action requires human support operations."
    elif unresolved_turn_count >= 2 or frustration["frustrated"]:
        escalation_recommended = True
        escalation_reason = "Repeated unresolved turns or user frustration detected."
    elif confidence < 0.5:
        escalation_recommended = True
        escalation_reason = "Low confidence support response."

    operational_summary = "Provided support workflow guidance with escalation checks."
    assumptions = [
        "The request is tied to standard support workflows unless account-specific actions are required."
    ]
    unresolved_info = ["Missing exact workflow step or screenshot context."] if not resolved else []
    memory_updates = (
        {"insurance_billing_status": "Potential claims or billing issue under investigation."}
        if "claim" in lower or "billing" in lower
        else {}
    )
    mode = "fallback"

    prompt = load_prompt("support.md")
    payload = await try_sdk_json(
        agent_name="Support Agent",
        instructions=(
            f"{prompt}\n\n"
            "Return valid JSON only with keys: answer, confidence, resolved, escalation_recommended, "
            "escalation_reason, handoff_to_sales, operational_summary, assumptions, unresolved_info, memory_updates."
        ),
        input_text=(
            "User request:\n"
            f"{user_message}\n\n"
            f"Clinic memory: {clinic_memory}\n"
            f"Help center results: {kb[:2]}\n"
            f"Billing FAQ results: {billing[:2]}\n"
            f"Upgrade options: {upgrades[:2]}\n"
            f"Unresolved turns: {unresolved_turn_count}\n"
            f"Account specific action requested: {account_specific}\n"
            f"Non-support growth or marketing request detected: {_is_growth_or_marketing_request(user_message)}\n"
            f"Frustration signal: {frustration}"
        ),
        tools=[search_help_center_tool, lookup_billing_faq_tool, lookup_upgrade_options_tool],
    )

    if payload:
        mode = "live_ai"
        answer = str(payload.get("answer") or answer)
        confidence = _to_float(payload.get("confidence"), confidence)
        resolved = _to_bool(payload.get("resolved"), resolved)
        escalation_recommended = _to_bool(payload.get("escalation_recommended"), escalation_recommended)
        escalation_reason_raw = payload.get("escalation_reason")
        escalation_reason = str(escalation_reason_raw).strip() if escalation_reason_raw else escalation_reason
        handoff_to_sales = _to_bool(payload.get("handoff_to_sales"), handoff_to_sales)
        operational_summary = str(payload.get("operational_summary") or operational_summary)
        assumptions = _to_str_list(payload.get("assumptions"), assumptions)
        unresolved_info = _to_str_list(payload.get("unresolved_info"), unresolved_info)
        memory_updates = _to_memory_updates(payload.get("memory_updates"), memory_updates)

    log_agent_event(
        agent="support_agent",
        workflow="support",
        mode=mode,
        detail={
            "resolved": resolved,
            "confidence": confidence,
            "escalation_recommended": escalation_recommended,
        },
    )

    return SupportResult(
        answer=answer,
        confidence=confidence,
        resolved=resolved,
        escalation_recommended=escalation_recommended,
        escalation_reason=escalation_reason,
        handoff_to_sales=handoff_to_sales,
        operational_summary=operational_summary,
        assumptions=assumptions,
        unresolved_info=unresolved_info,
        memory_updates=memory_updates,
    )
