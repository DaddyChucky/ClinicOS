from __future__ import annotations

import json

from app.agents.sdk import function_tool
from app.services.telemetry_service import log_tool_event
from app.services.campaign_service import CampaignService

campaign_service = CampaignService()


def identify_content_opportunities_data(pain_points: list[str], audience: str | None = None) -> dict:
    payload = {"opportunities": campaign_service.identify_content_opportunities(pain_points, audience)}
    log_tool_event(
        tool_name="identify_content_opportunities_data",
        payload={"pain_points": pain_points, "audience": audience},
        result=payload,
    )
    return payload


def generate_campaign_brief_data(audience: str, objective: str, pain_points: list[str]) -> dict:
    payload = campaign_service.generate_campaign_brief(audience, objective, pain_points)
    log_tool_event(
        tool_name="generate_campaign_brief_data",
        payload={"audience": audience, "objective": objective, "pain_points": pain_points},
        result=payload,
    )
    return payload


def generate_nurture_sequence_data(brief: dict) -> dict:
    payload = {"sequence": campaign_service.generate_nurture_sequence(brief)}
    log_tool_event(tool_name="generate_nurture_sequence_data", payload={"brief": brief}, result=payload)
    return payload


def save_campaign_draft_payload(payload: dict) -> dict:
    result = {"saved": True, "payload": payload}
    log_tool_event(tool_name="save_campaign_draft_payload", payload=payload, result=result)
    return result


@function_tool
def identify_content_opportunities(pain_points_csv: str, audience: str = "") -> str:
    pain_points = [item.strip() for item in pain_points_csv.split(",") if item.strip()]
    result = identify_content_opportunities_data(pain_points, audience or None)
    return json.dumps(result)


@function_tool
def generate_campaign_brief(audience: str, objective: str, pain_points_csv: str = "") -> str:
    pain_points = [item.strip() for item in pain_points_csv.split(",") if item.strip()]
    result = generate_campaign_brief_data(audience, objective, pain_points)
    return json.dumps(result)


@function_tool
def generate_nurture_sequence(
    audience: str,
    objective: str,
    key_message: str,
    proof_points_csv: str = "",
    pain_points_csv: str = "",
    cta: str = "",
) -> str:
    brief = {
        "audience": audience,
        "objective": objective,
        "key_message": key_message,
        "proof_points": [item.strip() for item in proof_points_csv.split(",") if item.strip()],
        "pain_points": [item.strip() for item in pain_points_csv.split(",") if item.strip()],
        "cta": cta or "Book a 20-minute workflow audit",
    }
    result = generate_nurture_sequence_data(brief)
    return json.dumps(result)


@function_tool
def save_campaign_draft(
    title: str,
    audience: str,
    channel: str,
    brief: str,
    nurture_sequence_json: str = "[]",
) -> str:
    try:
        nurture_sequence = json.loads(nurture_sequence_json)
    except json.JSONDecodeError:
        nurture_sequence = []
    payload = {
        "title": title,
        "audience": audience,
        "channel": channel,
        "brief": brief,
        "nurture_sequence": nurture_sequence,
    }
    result = save_campaign_draft_payload(payload)
    return json.dumps(result)
