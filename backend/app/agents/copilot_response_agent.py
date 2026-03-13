from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from app.agents.common import load_prompt, try_sdk_text
from app.services.telemetry_service import log_agent_event


@dataclass
class CopilotResponseResult:
    response: str
    mode: str


def _message_history(messages: Sequence[Any]) -> str:
    history: list[str] = []
    for message in messages[-8:]:
        role = str(getattr(message, "role", "assistant")).replace("_", " ").title()
        content = str(getattr(message, "content", "")).strip()
        if not content:
            continue
        history.append(f"{role}: {content[:700]}")
    return "\n\n".join(history)


def _draft_labels(drafts_created: list[Any]) -> list[str]:
    labels: list[str] = []
    for draft in drafts_created:
        draft_type = str(getattr(draft, "type", "") or "").replace("_", " ").strip()
        draft_id = getattr(draft, "id", None)
        if draft_id is None:
            continue
        labels.append(f"{draft_type or 'draft'} #{draft_id}")
    return labels


def _follow_up_prompts(clinic_memory: dict, task_packets: list[dict]) -> list[str]:
    prompts: list[str] = []
    field_prompts = {
        "Clinic name": "What should I call the practice in this plan?",
        "Practice type": "What kind of practice are you running?",
        "Location": "Which city or market should I plan around?",
        "Providers": "How many providers should this plan support?",
        "Front desk staff": "How many front-desk staff members are working this workflow?",
        "PMS software": "Which PMS or EHR is the team using today?",
        "Billing status": "What billing or claims issue should I account for in the next recommendation?",
    }

    for field in clinic_memory.get("missing_profile_fields", []):
        prompt = field_prompts.get(field)
        if prompt:
            prompts.append(prompt)

    for packet in task_packets:
        for detail in packet.get("unresolved_info", [])[:2]:
            cleaned = str(detail).strip()
            if cleaned:
                prompts.append(cleaned[0].upper() + cleaned[1:])

    deduped: list[str] = []
    seen: set[str] = set()
    for prompt in prompts:
        key = prompt.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(prompt.rstrip(".?") + "?")
    return deduped[:3]


def _track_summary(packet: dict) -> str:
    track = str(packet.get("track", "operations"))
    summary = str(packet.get("summary") or "").strip()
    if not summary:
        return ""
    if track == "support":
        return f"On the support side, {summary}"
    return f"Here is the support readout: {summary}"


def _fallback_response(
    *,
    clinic_memory: dict,
    task_packets: list[dict],
    review_required: bool,
    drafts_created: list[Any],
    escalation_recommended: bool,
    escalation_reason: str | None,
    escalation_summary: str | None,
    human_requested: bool,
    active_workflow: str,
) -> str:
    follow_ups = _follow_up_prompts(clinic_memory, task_packets)
    preferences = clinic_memory.get("response_preferences", [])
    completion_score = clinic_memory.get("profile_completion_score", 0)

    if active_workflow == "support":
        opening = "I focused first on the operational issue so we can stabilize the workflow before moving to anything else."
    else:
        opening = "I pulled together the support context in this chat and mapped the next best step from what you shared."

    updates = [summary for summary in (_track_summary(packet) for packet in task_packets) if summary]
    progress = " ".join(updates).strip()

    logistics_parts: list[str] = []
    draft_labels = _draft_labels(drafts_created)
    if review_required and draft_labels:
        logistics_parts.append(f"I also flagged {', '.join(draft_labels)} for internal review.")
    if escalation_recommended:
        handoff = escalation_summary or escalation_reason or "A human specialist should step in for the next part of this request."
        if human_requested:
            logistics_parts.append(f"I’ve prepared the human handoff so the team has the right context. {handoff}")
        else:
            logistics_parts.append(f"This looks like a good point for human support to step in. {handoff}")
    logistics = " ".join(logistics_parts).strip()

    guidance_parts: list[str] = []
    if follow_ups:
        guidance_parts.append("To tighten the next response, reply with:")
        guidance_parts.extend(f"- {prompt}" for prompt in follow_ups)
    elif completion_score < 100 and clinic_memory.get("missing_profile_fields"):
        guidance_parts.append(
            f"I can keep improving the recommendations as we fill in the remaining practice profile details, especially {clinic_memory['missing_profile_fields'][0].lower()}."
        )
    if preferences:
        guidance_parts.append(
            f"I’m also carrying forward your preference for {preferences[0].lower()} in this thread."
        )
    else:
        guidance_parts.append(
            "If you want, tell me whether the next reply should be more concise, more detailed, or more action-oriented and I’ll adjust."
        )

    parts = [opening]
    if progress:
        parts.append(progress)
    if logistics:
        parts.append(logistics)
    if guidance_parts:
        parts.append("\n".join(guidance_parts))
    return "\n\n".join(part for part in parts if part)


async def run_copilot_response(
    *,
    user_message: str,
    conversation_messages: Sequence[Any],
    clinic_memory: dict,
    task_packets: list[dict],
    review_required: bool,
    drafts_created: list[Any],
    escalation_recommended: bool,
    escalation_reason: str | None,
    escalation_summary: str | None,
    human_requested: bool,
    active_workflow: str,
    active_agent: str,
    confidence: float,
    loop_count: int,
    unresolved_turn_count: int,
) -> CopilotResponseResult:
    fallback = _fallback_response(
        clinic_memory=clinic_memory,
        task_packets=task_packets,
        review_required=review_required,
        drafts_created=drafts_created,
        escalation_recommended=escalation_recommended,
        escalation_reason=escalation_reason,
        escalation_summary=escalation_summary,
        human_requested=human_requested,
        active_workflow=active_workflow,
    )

    prompt = load_prompt("copilot_response.md")
    output = await try_sdk_text(
        agent_name="ClinicOS AI",
        instructions=prompt,
        input_text=(
            f"Latest user message:\n{user_message}\n\n"
            f"Recent thread:\n{_message_history(conversation_messages)}\n\n"
            f"Clinic memory:\n{clinic_memory}\n\n"
            f"Task packets:\n{task_packets}\n\n"
            f"Review required: {review_required}\n"
            f"Drafts created: {_draft_labels(drafts_created)}\n"
            f"Escalation recommended: {escalation_recommended}\n"
            f"Escalation reason: {escalation_reason}\n"
            f"Escalation summary: {escalation_summary}\n"
            f"Human explicitly requested: {human_requested}\n"
            f"Active workflow: {active_workflow}\n"
            f"Active agent: {active_agent}\n"
            f"Confidence: {confidence}\n"
            f"Loop count: {loop_count}\n"
            f"Unresolved turn count: {unresolved_turn_count}\n"
            f"Suggested follow-up questions: {_follow_up_prompts(clinic_memory, task_packets)}"
        ),
        tools=[],
    )

    response = str(output).strip() if output else fallback
    mode = "live_ai" if output else "fallback"
    log_agent_event(
        agent="clinicos_ai_response_agent",
        workflow=active_workflow,
        mode=mode,
        detail={
            "active_agent": active_agent,
            "confidence": confidence,
            "task_count": len(task_packets),
            "escalation_recommended": escalation_recommended,
        },
    )
    return CopilotResponseResult(response=response, mode=mode)
