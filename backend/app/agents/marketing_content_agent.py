from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.common import load_prompt, try_sdk_json
from app.services.telemetry_service import log_agent_event
from app.tools.marketing_tools import (
    generate_campaign_brief,
    generate_campaign_brief_data,
    generate_nurture_sequence,
    generate_nurture_sequence_data,
)


@dataclass
class MarketingContentResult:
    title: str
    audience: str
    channel: str
    brief: str
    nurture_sequence: list[dict]
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


def _to_sequence(value: object, default: list[dict]) -> list[dict]:
    if isinstance(value, list):
        sequence: list[dict] = []
        for item in value:
            if isinstance(item, dict):
                sequence.append({str(k): v for k, v in item.items()})
        return sequence or default
    return default


def _to_memory_updates(value: object, default: dict[str, str]) -> dict[str, str]:
    if isinstance(value, dict):
        payload: dict[str, str] = {}
        for key, item in value.items():
            if str(key).strip():
                payload[str(key)] = str(item)
        return payload or default
    return default


async def run_marketing_content(audience: str, objective: str, pain_points: list[str]) -> MarketingContentResult:
    brief_payload = generate_campaign_brief_data(audience, objective, pain_points)
    sequence_payload = generate_nurture_sequence_data(brief_payload)

    title = brief_payload["title"]
    channel = "email"
    brief_text = (
        f"Objective: {brief_payload['objective']}. "
        f"Key message: {brief_payload['key_message']} "
        f"Proof points: {', '.join(brief_payload['proof_points'])}. "
        f"CTA: {brief_payload['cta']}."
    )
    nurture_sequence = sequence_payload["sequence"]
    review_required = True
    operational_summary = "Built a campaign brief and nurture sequence for human review."
    assumptions = ["Campaign objective and pain points are accurate for this clinic segment."]
    unresolved_info = ["Final compliance checks and channel mix approval are still required."]
    memory_updates = {"marketing_activity": "Campaign brief drafted and queued for review."}
    mode = "fallback"

    prompt = load_prompt("marketing_content.md")
    payload = await try_sdk_json(
        agent_name="Marketing Content Agent",
        instructions=(
            f"{prompt}\n\n"
            "Return valid JSON only with keys: title, audience, channel, brief, nurture_sequence, review_required, "
            "operational_summary, assumptions, unresolved_info, memory_updates."
        ),
        input_text=(
            f"Audience: {audience}\n"
            f"Objective: {objective}\n"
            f"Pain points: {pain_points}\n"
            f"Fallback brief payload: {brief_payload}\n"
            f"Fallback nurture sequence: {nurture_sequence}"
        ),
        tools=[generate_campaign_brief, generate_nurture_sequence],
    )

    if payload:
        mode = "live_ai"
        title = str(payload.get("title") or title)
        audience = str(payload.get("audience") or audience)
        channel = str(payload.get("channel") or channel)
        brief_text = str(payload.get("brief") or brief_text)
        nurture_sequence = _to_sequence(payload.get("nurture_sequence"), nurture_sequence)
        review_required = _to_bool(payload.get("review_required"), review_required)
        operational_summary = str(payload.get("operational_summary") or operational_summary)
        assumptions = _to_str_list(payload.get("assumptions"), assumptions)
        unresolved_info = _to_str_list(payload.get("unresolved_info"), unresolved_info)
        memory_updates = _to_memory_updates(payload.get("memory_updates"), memory_updates)

    log_agent_event(
        agent="marketing_content_agent",
        workflow="marketing",
        mode=mode,
        detail={"title": title, "review_required": review_required},
    )

    return MarketingContentResult(
        title=title,
        audience=audience,
        channel=channel,
        brief=brief_text,
        nurture_sequence=nurture_sequence,
        review_required=review_required,
        operational_summary=operational_summary,
        assumptions=assumptions,
        unresolved_info=unresolved_info,
        memory_updates=memory_updates,
    )

