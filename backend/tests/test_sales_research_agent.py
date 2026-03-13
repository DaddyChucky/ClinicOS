from __future__ import annotations

import json

import pytest

from app.agents.sales_research_agent import run_sales_research
from app.tools import sales_tools


@pytest.mark.asyncio
async def test_sales_research_uses_live_payload_when_available(monkeypatch):
    captured: dict = {}

    async def fake_try_sdk_json(**kwargs):
        captured["tools"] = kwargs["tools"]
        return {
            "profile": {
                "clinic_name": "Harbor Kids Dental",
                "clinic_type": "dental",
                "specialty": "pediatric dentistry",
                "size_estimate": "4-8 providers",
                "location": "Portland, OR",
                "existing_lead": False,
                "pain_points": [
                    "parent intake paperwork creates check-in bottlenecks",
                    "recall reminders need better timing around family schedules",
                ],
                "signals": [
                    "online forms page is live on the public website",
                    "same-day emergency language suggests volatile schedule management",
                ],
            },
            "fit_score": 88,
            "fit_reasons": [
                "Operating signals indicate active change pressure: online forms page is live on the public website.",
                "Pain-point density and live operating signals both suggest a strong workflow fit.",
            ],
            "summary": "Live research found strong pediatric dental workflow signals and a high ICP match.",
            "handoff_to_marketing": True,
            "operational_summary": "Used live web research plus public-page scraping.",
            "assumptions": ["Public website messaging was used as a proxy for current workflow design."],
            "unresolved_info": ["Decision-maker and software stack still need confirmation."],
            "memory_updates": {"clinic_name": "Harbor Kids Dental", "practice_type": "pediatric dentistry"},
        }

    monkeypatch.setattr("app.agents.sales_research_agent.try_sdk_json", fake_try_sdk_json)

    result = await run_sales_research(
        user_message="Research Harbor Kids Dental",
        clinic_name="Harbor Kids Dental",
        location="Portland, OR",
    )

    assert result.profile["specialty"] == "pediatric dentistry"
    assert result.fit_score == 88
    assert result.handoff_to_marketing is True
    assert any(tool.__class__.__name__ == "WebSearchTool" for tool in captured["tools"])
    assert any(getattr(tool, "__name__", "") == "scrape_public_page" for tool in captured["tools"])


def test_scrape_public_page_serializes_snapshot(monkeypatch):
    monkeypatch.setattr(
        sales_tools,
        "scrape_page_snapshot",
        lambda url: {
            "url": url,
            "final_url": url,
            "title": "Example Clinic",
            "headings": ["Online Forms", "Book an Appointment"],
            "text_excerpt": "Online forms and appointment booking are available.",
        },
    )

    payload = json.loads(sales_tools.scrape_public_page("https://example.com"))

    assert payload["title"] == "Example Clinic"
    assert "Online Forms" in payload["headings"]
