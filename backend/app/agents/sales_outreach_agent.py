from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.common import load_prompt, try_sdk_json
from app.services.telemetry_service import log_agent_event
from app.tools.sales_tools import build_outreach_draft, generate_outreach_draft


@dataclass
class SalesOutreachResult:
    subject: str
    body: str
    tone: str
    personalization_notes: str
    review_required: bool
    operational_summary: str = ""
    assumptions: list[str] = field(default_factory=list)
    unresolved_info: list[str] = field(default_factory=list)
    memory_updates: dict[str, str] = field(default_factory=dict)


def _to_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in {"true", "yes", "1"}:
            return True
        if value.lower() in {"false", "no", "0"}:
            return False
    return default


def _to_str_list(value: object, default: list[str]) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or default
    return default


def _to_memory_updates(value: object, default: dict[str, str]) -> dict[str, str]:
    if isinstance(value, dict):
        payload: dict[str, str] = {}
        for key, item in value.items():
            if str(key).strip():
                payload[str(key)] = str(item)
        return payload or default
    return default


async def run_sales_outreach(profile: dict, fit_score: float, fit_reasons: list[str]) -> SalesOutreachResult:
    draft = build_outreach_draft(profile, fit_score, fit_reasons)
    subject = draft["subject"]
    body = draft["body"]
    tone = draft["tone"]
    personalization_notes = draft["personalization_notes"]
    review_required = True
    operational_summary = "Prepared an outreach draft for human review before any external send."
    assumptions = ["Prospect pains and ICP fit were used to personalize positioning."]
    unresolved_info = ["Final offer and CTA should be validated by account owner."]
    memory_updates = {"prior_sales_interaction": "Outreach draft created and queued for review."}
    mode = "fallback"

    prompt = load_prompt("sales_outreach.md")
    payload = await try_sdk_json(
        agent_name="Sales Outreach Agent",
        instructions=(
            f"{prompt}\n\n"
            "Return valid JSON only with keys: subject, body, tone, personalization_notes, review_required, "
            "operational_summary, assumptions, unresolved_info, memory_updates."
        ),
        input_text=(
            f"Clinic profile: {profile}\n"
            f"Fit score: {fit_score}\n"
            f"Fit reasons: {fit_reasons}\n"
            "Write a high-quality outreach draft that sounds human and specific."
        ),
        tools=[generate_outreach_draft],
    )

    if payload:
        mode = "live_ai"
        subject = str(payload.get("subject") or subject)
        body = str(payload.get("body") or body)
        tone = str(payload.get("tone") or tone)
        personalization_notes = str(payload.get("personalization_notes") or personalization_notes)
        review_required = _to_bool(payload.get("review_required"), review_required)
        operational_summary = str(payload.get("operational_summary") or operational_summary)
        assumptions = _to_str_list(payload.get("assumptions"), assumptions)
        unresolved_info = _to_str_list(payload.get("unresolved_info"), unresolved_info)
        memory_updates = _to_memory_updates(payload.get("memory_updates"), memory_updates)

    log_agent_event(
        agent="sales_outreach_agent",
        workflow="sales",
        mode=mode,
        detail={"fit_score": fit_score, "review_required": review_required},
    )

    return SalesOutreachResult(
        subject=subject,
        body=body,
        tone=tone,
        personalization_notes=personalization_notes,
        review_required=review_required,
        operational_summary=operational_summary,
        assumptions=assumptions,
        unresolved_info=unresolved_info,
        memory_updates=memory_updates,
    )

