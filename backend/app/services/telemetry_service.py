from __future__ import annotations

import json
import logging
from typing import Any


logger = logging.getLogger("ops-pilot.telemetry")


def _compact(payload: Any, limit: int = 320) -> str:
    try:
        text = json.dumps(payload, default=str)
    except Exception:
        text = str(payload)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def log_openai_event(*, event: str, agent: str, detail: dict[str, Any]) -> None:
    logger.info("openai.%s agent=%s detail=%s", event, agent, _compact(detail))


def log_tool_event(*, tool_name: str, payload: dict[str, Any], result: Any) -> None:
    logger.info("tool.call name=%s payload=%s result=%s", tool_name, _compact(payload), _compact(result))


def log_agent_event(*, agent: str, workflow: str, mode: str, detail: dict[str, Any] | None = None) -> None:
    logger.info("agent.run agent=%s workflow=%s mode=%s detail=%s", agent, workflow, mode, _compact(detail or {}))

