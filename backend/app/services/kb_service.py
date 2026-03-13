from __future__ import annotations

import json
from pathlib import Path


class KBService:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path(__file__).resolve().parent.parent / "data"
        self.kb_articles = self._load_json("kb_articles.json")
        self.billing_faqs = self._load_json("billing_faqs.json")
        self.upgrade_plans = self._load_json("upgrade_plans.json")

    def _load_json(self, filename: str) -> list[dict]:
        path = self.data_dir / filename
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def search_help_center(self, query: str, limit: int = 3) -> list[dict]:
        query_tokens = set(query.lower().split())
        scored: list[tuple[int, dict]] = []

        for article in self.kb_articles:
            haystack = f"{article['title']} {article['summary']} {article['content']}".lower()
            score = sum(1 for token in query_tokens if token in haystack)
            if score > 0:
                scored.append((score, article))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def lookup_billing_faq(self, query: str) -> list[dict]:
        query_tokens = set(query.lower().split())
        matches = []
        for faq in self.billing_faqs:
            haystack = f"{faq['question']} {faq['answer']}".lower()
            if any(token in haystack for token in query_tokens):
                matches.append(faq)
        return matches[:3]

    def lookup_upgrade_options(self, query: str) -> list[dict]:
        query_lower = query.lower()
        matches = [
            plan
            for plan in self.upgrade_plans
            if plan["name"].lower() in query_lower
            or any(keyword in query_lower for keyword in plan.get("keywords", []))
            or "upgrade" in query_lower
        ]
        return matches[:3]
