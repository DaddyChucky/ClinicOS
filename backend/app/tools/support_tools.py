from __future__ import annotations

import json

from app.agents.sdk import function_tool
from app.services.telemetry_service import log_tool_event
from app.services.kb_service import KBService

kb_service = KBService()


def search_help_center(query: str) -> dict:
    results = kb_service.search_help_center(query)
    payload = {"results": results}
    log_tool_event(tool_name="search_help_center", payload={"query": query}, result=payload)
    return payload


def lookup_billing_faq(query: str) -> dict:
    results = kb_service.lookup_billing_faq(query)
    payload = {"results": results}
    log_tool_event(tool_name="lookup_billing_faq", payload={"query": query}, result=payload)
    return payload


def lookup_upgrade_options(query: str) -> dict:
    results = kb_service.lookup_upgrade_options(query)
    payload = {"results": results}
    log_tool_event(tool_name="lookup_upgrade_options", payload={"query": query}, result=payload)
    return payload


def create_support_escalation(reason: str, summary: str) -> dict:
    payload = {"reason": reason, "summary": summary, "action": "escalation_recommended"}
    log_tool_event(tool_name="create_support_escalation", payload={"reason": reason}, result=payload)
    return payload


@function_tool
def search_help_center_tool(query: str) -> str:
    return json.dumps(search_help_center(query))


@function_tool
def lookup_billing_faq_tool(query: str) -> str:
    return json.dumps(lookup_billing_faq(query))


@function_tool
def lookup_upgrade_options_tool(query: str) -> str:
    return json.dumps(lookup_upgrade_options(query))


@function_tool
def create_support_escalation_tool(reason: str, summary: str) -> str:
    return json.dumps(create_support_escalation(reason, summary))
