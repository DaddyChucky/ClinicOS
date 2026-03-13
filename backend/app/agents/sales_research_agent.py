from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.agents.common import load_prompt, try_sdk_json
from app.config import get_settings
from app.services.telemetry_service import log_agent_event
from app.tools.sales_tools import (
    research_clinic,
    research_clinic_profile,
    scrape_public_page,
    score_icp_fit,
    score_icp_profile,
)


@dataclass
class SalesResearchResult:
    profile: dict
    fit_score: float
    fit_reasons: list[str]
    summary: str
    handoff_to_marketing: bool
    operational_summary: str = ""
    assumptions: list[str] = field(default_factory=list)
    unresolved_info: list[str] = field(default_factory=list)
    memory_updates: dict[str, str] = field(default_factory=dict)


def extract_clinic_name(text: str) -> str | None:
    quoted = re.findall(r'"([^"]+)"', text)
    if quoted:
        return quoted[0]

    patterns = [
        r"for\s+([A-Z][a-zA-Z0-9\s&\-]+\s(?:Clinic|Dental|Medical|Care|Health))",
        r"at\s+([A-Z][a-zA-Z0-9\s&\-]+\s(?:Clinic|Dental|Medical|Care|Health))",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def _to_float(value: object, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(0.0, min(100.0, round(parsed, 1)))


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


def _to_profile(value: object, default: dict) -> dict:
    if not isinstance(value, dict):
        return default
    payload = {str(k): v for k, v in value.items()}
    if not payload.get("clinic_name") or not payload.get("clinic_type"):
        return default
    if "pain_points" in payload and not isinstance(payload["pain_points"], list):
        payload["pain_points"] = [str(payload["pain_points"])]
    if "signals" in payload and not isinstance(payload["signals"], list):
        payload["signals"] = [str(payload["signals"])]
    return payload


def _to_memory_updates(value: object, default: dict[str, str]) -> dict[str, str]:
    if isinstance(value, dict):
        payload: dict[str, str] = {}
        for key, item in value.items():
            if str(key).strip():
                payload[str(key)] = str(item)
        return payload or default
    return default


def _sales_research_tools() -> list:
    tools: list = [research_clinic, scrape_public_page, score_icp_fit]
    settings = get_settings()
    if not settings.enable_live_sales_research:
        return tools
    try:
        from agents import WebSearchTool

        return [WebSearchTool(search_context_size="high"), *tools]
    except Exception:
        return tools


async def run_sales_research(
    user_message: str,
    clinic_name: str | None = None,
    location: str | None = None,
    clinic_memory: dict | None = None,
) -> SalesResearchResult:
    clinic_memory = clinic_memory or {}
    name = clinic_name or extract_clinic_name(user_message) or "Sunrise Family Dental"
    resolved_location = location or clinic_memory.get("location")
    profile = research_clinic_profile(name, resolved_location)
    scoring = score_icp_profile(profile)
    fit_score = scoring["fit_score"]
    fit_reasons = scoring["reasons"]
    signal_summary = ", ".join(profile.get("signals", [])[:2])

    summary = (
        f"Prospect: {profile['clinic_name']} ({profile['clinic_type']}, {profile.get('specialty', 'general')}). "
        f"Estimated size: {profile.get('size_estimate', 'unknown')}. "
        f"Likely pain points: {', '.join(profile.get('pain_points', []))}. "
        f"{f'Observed operating signals: {signal_summary}. ' if signal_summary else ''}"
        f"ICP fit score: {fit_score}/100."
    )

    handoff_to_marketing = bool(profile.get("pain_points")) and fit_score >= 65
    operational_summary = "Generated clinic profile and ICP fit score for sales qualification."
    assumptions = [
        "Clinic profile was inferred from available research inputs.",
        "Pain points reflect likely operational bottlenecks, not confirmed account telemetry.",
    ]
    unresolved_info = (
        ["Need confirmed decision-maker and budget window."] if fit_score >= 65 else ["Need stronger qualification signals."]
    )
    memory_updates = {
        "clinic_name": profile["clinic_name"],
        "practice_type": profile.get("specialty") or profile.get("clinic_type"),
    }
    mode = "fallback"

    prompt = load_prompt("sales_research.md")
    payload = await try_sdk_json(
        agent_name="Sales Research Agent",
        instructions=(
            f"{prompt}\n\n"
            "Return valid JSON only with keys: profile, fit_score, fit_reasons, summary, handoff_to_marketing, "
            "operational_summary, assumptions, unresolved_info, memory_updates.\n"
            "When live AI is available, use web search to research the clinic online before returning your answer. "
            "Use scrape_public_page for any official site or relevant public page you need to inspect more closely. "
            "Do not fabricate facts. If information is inferred rather than directly observed, say so plainly."
        ),
        input_text=(
            "User request:\n"
            f"{user_message}\n\n"
            f"Clinic memory: {clinic_memory}\n"
            f"Inferred clinic name: {name}\n"
            f"Inferred location: {resolved_location}\n"
            f"Fallback research profile: {profile}\n"
            f"Fallback fit score: {fit_score}\n"
            f"Fallback fit reasons: {fit_reasons}\n"
            "Research goal: determine clinic type, specialty, size estimate, likely workflow pain points, "
            "operating signals, and an evidence-based ICP fit estimate for ClinicOS."
        ),
        tools=_sales_research_tools(),
    )

    if payload:
        mode = "live_ai"
        profile = _to_profile(payload.get("profile"), profile)
        if resolved_location and not profile.get("location"):
            profile["location"] = resolved_location
        fit_score = _to_float(payload.get("fit_score"), fit_score)
        fit_reasons = _to_str_list(payload.get("fit_reasons"), fit_reasons)
        summary = str(payload.get("summary") or summary)
        handoff_to_marketing = _to_bool(payload.get("handoff_to_marketing"), handoff_to_marketing)
        operational_summary = str(payload.get("operational_summary") or operational_summary)
        assumptions = _to_str_list(payload.get("assumptions"), assumptions)
        unresolved_info = _to_str_list(payload.get("unresolved_info"), unresolved_info)
        memory_updates = _to_memory_updates(payload.get("memory_updates"), memory_updates)

    log_agent_event(
        agent="sales_research_agent",
        workflow="sales",
        mode=mode,
        detail={"clinic_name": profile.get("clinic_name"), "fit_score": fit_score},
    )

    return SalesResearchResult(
        profile=profile,
        fit_score=fit_score,
        fit_reasons=fit_reasons,
        summary=summary,
        handoff_to_marketing=handoff_to_marketing,
        operational_summary=operational_summary,
        assumptions=assumptions,
        unresolved_info=unresolved_info,
        memory_updates=memory_updates,
    )
