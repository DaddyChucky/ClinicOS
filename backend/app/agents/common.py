from __future__ import annotations

import json
import re
from pathlib import Path

from app.agents.sdk import Agent, Runner, SDK_AVAILABLE
from app.config import get_settings
from app.services.telemetry_service import log_openai_event

settings = get_settings()


def load_prompt(filename: str) -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / filename
    with prompt_path.open("r", encoding="utf-8") as f:
        return f.read()


async def try_sdk_text(agent_name: str, instructions: str, input_text: str, tools: list) -> str | None:
    if not SDK_AVAILABLE:
        log_openai_event(
            event="fallback",
            agent=agent_name,
            detail={"reason": "sdk_unavailable"},
        )
        return None

    if not settings.openai_api_key:
        log_openai_event(
            event="fallback",
            agent=agent_name,
            detail={"reason": "missing_api_key"},
        )
        return None

    try:
        log_openai_event(
            event="attempt",
            agent=agent_name,
            detail={"model": settings.openai_model},
        )
        agent = Agent(
            name=agent_name,
            instructions=instructions,
            tools=tools,
            model=settings.openai_model,
        )
        result = await Runner.run(agent, input=input_text)
        output = getattr(result, "final_output", None)
        if output is None:
            log_openai_event(
                event="fallback",
                agent=agent_name,
                detail={"reason": "empty_response"},
            )
            return None
        log_openai_event(
            event="used",
            agent=agent_name,
            detail={"model": settings.openai_model},
        )
        return str(output)
    except Exception as exc:
        log_openai_event(
            event="fallback",
            agent=agent_name,
            detail={"reason": "runtime_error", "error": str(exc)},
        )
        return None


def runtime_status() -> dict:
    api_key_loaded = bool(settings.openai_api_key)
    return {
        "sdk_available": SDK_AVAILABLE,
        "api_key_loaded": api_key_loaded,
        "model": settings.openai_model,
        "live_mode_ready": SDK_AVAILABLE and api_key_loaded,
    }


def _extract_json_blob(text: str) -> str | None:
    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return None


async def try_sdk_json(
    *,
    agent_name: str,
    instructions: str,
    input_text: str,
    tools: list,
) -> dict | None:
    output = await try_sdk_text(
        agent_name=agent_name,
        instructions=instructions,
        input_text=input_text,
        tools=tools,
    )
    if not output:
        return None

    json_blob = _extract_json_blob(output)
    if not json_blob:
        log_openai_event(
            event="fallback",
            agent=agent_name,
            detail={"reason": "json_not_found"},
        )
        return None

    try:
        payload = json.loads(json_blob)
    except json.JSONDecodeError as exc:
        log_openai_event(
            event="fallback",
            agent=agent_name,
            detail={"reason": "json_parse_failed", "error": str(exc)},
        )
        return None

    if not isinstance(payload, dict):
        log_openai_event(
            event="fallback",
            agent=agent_name,
            detail={"reason": "json_not_object"},
        )
        return None
    return payload
