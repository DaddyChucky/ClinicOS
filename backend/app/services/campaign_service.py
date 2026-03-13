from __future__ import annotations

import json
from pathlib import Path


class CampaignService:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path(__file__).resolve().parent.parent / "data"
        self.personas = self._load_json("marketing_personas.json")
        self.examples = self._load_json("campaign_examples.json")

    def _load_json(self, filename: str) -> list[dict]:
        path = self.data_dir / filename
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def identify_content_opportunities(self, pains: list[str], audience: str | None = None) -> list[str]:
        opportunities = []
        for pain in pains:
            opportunities.append(f"How-to content addressing: {pain}")
            opportunities.append(f"Benchmark guide: reducing '{pain}' in clinics")

        if audience:
            opportunities.append(f"Role-specific checklist for {audience}")

        # Deduplicate while preserving order.
        deduped = list(dict.fromkeys(opportunities))
        return deduped[:6]

    def generate_campaign_brief(self, audience: str, objective: str, pain_points: list[str]) -> dict:
        top_examples = self.examples[:2]
        headline = f"{objective}: Practical workflows for {audience}"
        key_message = (
            "Show clinic teams how to reduce admin burden while improving patient throughput "
            "with repeatable front-desk and billing workflows."
        )
        cta = "Book a 20-minute workflow audit"

        return {
            "title": headline,
            "audience": audience,
            "objective": objective,
            "key_message": key_message,
            "pain_points": pain_points,
            "proof_points": [example["hook"] for example in top_examples],
            "cta": cta,
        }

    def generate_nurture_sequence(self, brief: dict) -> list[dict]:
        audience = brief.get("audience", "clinic operations leaders")
        objective = brief.get("objective", "Drive product evaluation")
        pains = brief.get("pain_points", [])
        pain_line = pains[0] if pains else "front-desk bottlenecks"

        return [
            {
                "step": 1,
                "subject": f"{audience}: quick win for {pain_line}",
                "body": (
                    f"We see {audience} teams lose hours each week to {pain_line}. "
                    "Here is a 3-step workflow to fix it in under 30 minutes."
                ),
                "goal": "Awareness",
            },
            {
                "step": 2,
                "subject": "Template: patient follow-up flow that actually gets used",
                "body": (
                    "Sharing the exact checklist our highest-retention clinics use for billing follow-up "
                    "and recall reminders without adding headcount."
                ),
                "goal": "Education",
            },
            {
                "step": 3,
                "subject": f"{objective} with operational proof",
                "body": (
                    "If useful, we can map this framework to your clinic's current stack and "
                    "identify where automation pays back first."
                ),
                "goal": "Conversion",
            },
        ]
