from __future__ import annotations

import hashlib
import json

from app.agents.sdk import function_tool
from app.services.telemetry_service import log_tool_event
from app.services.prospect_service import ProspectService
from app.services.scoring_service import ScoringService
from app.services.web_scrape_service import scrape_page_snapshot

prospect_service = ProspectService()
scoring_service = ScoringService()


def research_clinic_profile(clinic_name: str, location: str | None = None) -> dict:
    payload = prospect_service.research_clinic(clinic_name=clinic_name, location=location)
    log_tool_event(
        tool_name="research_clinic_profile",
        payload={"clinic_name": clinic_name, "location": location},
        result=payload,
    )
    return payload


def score_icp_profile(profile: dict) -> dict:
    score, reasons = scoring_service.score_icp_fit(profile)
    payload = {"fit_score": score, "reasons": reasons}
    log_tool_event(tool_name="score_icp_profile", payload={"profile": profile}, result=payload)
    return payload


def build_outreach_draft(profile: dict, fit_score: float, reasons: list[str]) -> dict:
    clinic_name = profile.get("clinic_name", "your clinic")
    specialty = profile.get("specialty") or profile.get("clinic_type", "your specialty")
    location = profile.get("location")
    pain_points = profile.get("pain_points", [])
    signals = profile.get("signals", [])
    top_pain = pain_points[0] if pain_points else "manual admin load"
    second_pain = pain_points[1] if len(pain_points) > 1 else "follow-up work spilling back to staff"
    top_signal = signals[0] if signals else "public operating signals point to workflow strain"
    market_context = f" in {location}" if location else ""
    proof_point = reasons[0] if reasons else "front-desk coordination and follow-up often create unnecessary friction"
    variant_seed = f"{clinic_name.lower()}::{specialty.lower()}::{(location or '').lower()}"
    variant = int(hashlib.sha256(variant_seed.encode("utf-8")).hexdigest()[:6], 16) % 3

    if variant == 0:
        subject = f"{clinic_name}: reducing {top_pain}"
        body = (
            f"Hi team at {clinic_name},\n\n"
            f"I was looking at {specialty} practices{market_context} and noticed signals that usually show up when {top_pain} and {second_pain} start pulling too much time back onto the front desk. "
            f"In your case, {top_signal.lower()}.\n\n"
            f"ClinicOS helps practices tighten recall, intake, scheduling, and billing follow-up without asking staff to take on another tool that creates more clicks. {proof_point}.\n\n"
            "If helpful, I can send a short workflow idea for where teams usually start and what gets automated first.\n\n"
            "- ClinicOS Team"
        )
    elif variant == 1:
        subject = f"Idea for {clinic_name}'s {specialty} workflow stack"
        body = (
            f"Hi {clinic_name} team,\n\n"
            f"Reaching out because {top_signal.lower()}, and that often lines up with teams feeling the drag from {top_pain}. "
            f"For {specialty} groups{market_context}, that pressure tends to spread into {second_pain} pretty quickly.\n\n"
            "ClinicOS is built for practices that want tighter handoffs across intake, follow-up, billing, and patient communications while keeping human review where it matters. "
            f"From the outside, it looks like there may be a strong fit here. {proof_point}.\n\n"
            "Open to a quick note with two or three ideas tailored to your workflow?\n\n"
            "- ClinicOS Team"
        )
    else:
        subject = f"{clinic_name} and the ops drag behind {top_pain}"
        body = (
            f"Hi team,\n\n"
            f"I spent a little time looking at {clinic_name}{market_context}. Between {top_signal.lower()} and the way {specialty} operations usually scale, "
            f"there is a good chance the team is dealing with both {top_pain} and {second_pain}.\n\n"
            f"ClinicOS helps dental and medical practices remove that admin drag across the front desk and back office. {proof_point}.\n\n"
            "If you want, I can share a short before-and-after example of how practices use it to reduce missed follow-up work without losing control of the process.\n\n"
            "- ClinicOS Team"
        )

    notes = " | ".join([*signals[:2], *reasons[:2]]) if signals else " | ".join(reasons[:3])
    payload = {
        "subject": subject,
        "body": body,
        "tone": "consultative",
        "personalization_notes": notes,
        "fit_score": fit_score,
    }
    log_tool_event(
        tool_name="build_outreach_draft",
        payload={"profile": profile, "fit_score": fit_score, "reasons": reasons},
        result=payload,
    )
    return payload


def save_outreach_draft_payload(payload: dict) -> dict:
    result = {"saved": True, "payload": payload}
    log_tool_event(tool_name="save_outreach_draft_payload", payload=payload, result=result)
    return result


@function_tool
def research_clinic(clinic_name: str, location: str = "") -> str:
    result = research_clinic_profile(clinic_name=clinic_name, location=location or None)
    return json.dumps(result)


@function_tool
def scrape_public_page(url: str) -> str:
    result = scrape_page_snapshot(url)
    log_tool_event(tool_name="scrape_public_page", payload={"url": url}, result=result)
    return json.dumps(result)


@function_tool
def score_icp_fit(
    clinic_type: str,
    specialty: str,
    size_estimate: str,
    pain_points_csv: str = "",
    signals_csv: str = "",
    existing_lead: bool = False,
) -> str:
    profile = {
        "clinic_type": clinic_type,
        "specialty": specialty,
        "size_estimate": size_estimate,
        "pain_points": [item.strip() for item in pain_points_csv.split(",") if item.strip()],
        "signals": [item.strip() for item in signals_csv.split("|") if item.strip()],
        "existing_lead": existing_lead,
    }
    result = score_icp_profile(profile)
    return json.dumps(result)


@function_tool
def generate_outreach_draft(
    clinic_name: str,
    specialty: str,
    top_pain: str,
    fit_score: float,
    reasons_csv: str = "",
) -> str:
    reasons = [item.strip() for item in reasons_csv.split("|") if item.strip()]
    profile = {
        "clinic_name": clinic_name,
        "specialty": specialty,
        "pain_points": [top_pain] if top_pain else [],
    }
    draft = build_outreach_draft(profile, fit_score, reasons)
    return json.dumps(draft)


@function_tool
def save_outreach_draft(
    subject: str,
    body: str,
    tone: str = "consultative",
    personalization_notes: str = "",
) -> str:
    payload = {
        "subject": subject,
        "body": body,
        "tone": tone,
        "personalization_notes": personalization_notes,
    }
    result = save_outreach_draft_payload(payload)
    return json.dumps(result)
