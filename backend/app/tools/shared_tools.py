from __future__ import annotations

import json
import re

from app.agents.sdk import function_tool
from app.services.telemetry_service import log_tool_event


HUMAN_KEYWORDS = {
    "human",
    "person",
    "agent",
    "representative",
    "someone",
    "call me",
    "talk to",
}

FRUSTRATION_PATTERNS = [
    r"this isn't helping",
    r"still not fixed",
    r"frustrat",
    r"angry",
    r"useless",
    r"running in circles",
    r"again\?",
]


def identify_user_role(text: str) -> str:
    lower = text.lower()
    role = "unknown"
    if any(term in lower for term in ["i'm in sales", "sales rep", "pipeline", "lead list"]):
        role = "internal_sales_rep"
    elif any(term in lower for term in ["marketing", "campaign", "nurture", "persona"]):
        role = "internal_marketing_user"
    elif any(term in lower for term in ["we are a customer", "our account", "our subscription", "our clinic uses"]):
        role = "existing_customer"
    elif any(term in lower for term in ["evaluating", "not a customer", "considering", "demo"]):
        role = "external_prospect"
    log_tool_event(tool_name="identify_user_role", payload={"text": text}, result={"role": role})
    return role


def detect_frustration(text: str) -> dict:
    lower = text.lower()
    score = 0.0

    if any(keyword in lower for keyword in HUMAN_KEYWORDS):
        score += 0.35
    for pattern in FRUSTRATION_PATTERNS:
        if re.search(pattern, lower):
            score += 0.25
    if "!" in text:
        score += 0.1

    score = min(score, 1.0)
    payload = {"frustration_score": round(score, 2), "frustrated": score >= 0.45}
    log_tool_event(tool_name="detect_frustration", payload={"text": text}, result=payload)
    return payload


def create_handoff_summary(from_agent: str, to_agent: str, reason: str, context: str) -> str:
    payload = (
        f"Handoff from {from_agent} to {to_agent}. "
        f"Reason: {reason}. Context: {context[:350]}"
    )
    log_tool_event(
        tool_name="create_handoff_summary",
        payload={"from_agent": from_agent, "to_agent": to_agent, "reason": reason},
        result={"summary": payload},
    )
    return payload


def explicit_human_request(text: str) -> bool:
    lower = text.lower()
    requested = any(keyword in lower for keyword in ["talk to human", "human", "person", "call me", "live agent"])
    log_tool_event(tool_name="explicit_human_request", payload={"text": text}, result={"requested": requested})
    return requested


@function_tool
def identify_user_role_tool(text: str) -> str:
    return identify_user_role(text)


@function_tool
def detect_frustration_tool(text: str) -> str:
    return json.dumps(detect_frustration(text))


@function_tool
def create_handoff_summary_tool(from_agent: str, to_agent: str, reason: str, context: str) -> str:
    return create_handoff_summary(from_agent, to_agent, reason, context)
