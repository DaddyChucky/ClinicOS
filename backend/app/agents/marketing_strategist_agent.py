from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.common import load_prompt, try_sdk_json
from app.services.telemetry_service import log_agent_event
from app.tools.marketing_tools import identify_content_opportunities, identify_content_opportunities_data


@dataclass
class MarketingStrategyResult:
    opportunities: list[str]
    recommendation: str
    operational_summary: str = ""
    assumptions: list[str] = field(default_factory=list)
    unresolved_info: list[str] = field(default_factory=list)
    memory_updates: dict[str, str] = field(default_factory=dict)


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


async def run_marketing_strategist(
    user_message: str,
    audience: str = "office managers and front desk leads",
    pain_points: list[str] | None = None,
) -> MarketingStrategyResult:
    pain_points = pain_points or [
        "manual patient reminders",
        "insurance follow-up delays",
        "front desk scheduling bottlenecks",
    ]
    opportunities = identify_content_opportunities_data(pain_points, audience)["opportunities"]
    recommendation = (
        "Prioritize workflow-based educational content, then retarget engaged clinics with "
        "ROI-focused nurture messaging tied to billing and front-desk efficiency gains."
    )
    operational_summary = "Identified campaign opportunity themes tied to clinic pain points."
    assumptions = ["Audience and pain points reflect current clinic context shared in conversation."]
    unresolved_info = ["Need channel-level budget constraints and launch window."]
    memory_updates = {"growth_signal": "Marketing campaign planning initiated."}
    mode = "fallback"

    prompt = load_prompt("marketing_strategist.md")
    payload = await try_sdk_json(
        agent_name="Marketing Strategist Agent",
        instructions=(
            f"{prompt}\n\n"
            "Return valid JSON only with keys: opportunities, recommendation, operational_summary, "
            "assumptions, unresolved_info, memory_updates."
        ),
        input_text=(
            f"User request: {user_message}\n"
            f"Audience: {audience}\n"
            f"Pain points: {pain_points}\n"
            f"Fallback opportunities: {opportunities}"
        ),
        tools=[identify_content_opportunities],
    )

    if payload:
        mode = "live_ai"
        opportunities = _to_str_list(payload.get("opportunities"), opportunities)
        recommendation = str(payload.get("recommendation") or recommendation)
        operational_summary = str(payload.get("operational_summary") or operational_summary)
        assumptions = _to_str_list(payload.get("assumptions"), assumptions)
        unresolved_info = _to_str_list(payload.get("unresolved_info"), unresolved_info)
        memory_updates = _to_memory_updates(payload.get("memory_updates"), memory_updates)

    log_agent_event(
        agent="marketing_strategist_agent",
        workflow="marketing",
        mode=mode,
        detail={"opportunity_count": len(opportunities)},
    )

    return MarketingStrategyResult(
        opportunities=opportunities,
        recommendation=recommendation,
        operational_summary=operational_summary,
        assumptions=assumptions,
        unresolved_info=unresolved_info,
        memory_updates=memory_updates,
    )

