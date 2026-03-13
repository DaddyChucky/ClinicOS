from __future__ import annotations

import json
from pathlib import Path


class ScoringService:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path(__file__).resolve().parent.parent / "data"
        self.rules = self._load_json("icp_rules.json")

    def _load_json(self, filename: str) -> dict:
        path = self.data_dir / filename
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def score_icp_fit(self, profile: dict) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []

        clinic_type = (profile.get("clinic_type") or "").lower()
        specialty = (profile.get("specialty") or "").lower()
        size_estimate = (profile.get("size_estimate") or "").lower()
        pain_points = [p.lower() for p in profile.get("pain_points", [])]
        signals = [s.lower() for s in profile.get("signals", [])]
        existing_lead = bool(profile.get("existing_lead"))

        type_weights: dict[str, float] = self.rules.get("clinic_type_weights", {})
        specialty_weights: dict[str, float] = self.rules.get("specialty_weights", {})
        size_weights: dict[str, float] = self.rules.get("size_weights", {})

        for key, weight in type_weights.items():
            if key in clinic_type:
                score += float(weight)
                reasons.append(f"Clinic type aligns with ICP ({key}).")

        for key, weight in specialty_weights.items():
            if key in specialty:
                score += float(weight)
                reasons.append(f"Specialty fit ({key}).")

        for key, weight in size_weights.items():
            if key in size_estimate:
                score += float(weight)
                reasons.append(f"Organization size fit ({key}).")

        high_value_pains = self.rules.get("high_value_pain_points", [])
        pain_hits = [pain for pain in high_value_pains if any(pain in p for p in pain_points)]
        if pain_hits:
            score += min(20.0, 4.0 * len(pain_hits))
            reasons.append(f"Detected high-value pains: {', '.join(pain_hits[:3])}.")

        signal_keywords = {
            "hiring": 4.0,
            "career": 4.0,
            "expanded": 5.0,
            "second location": 5.0,
            "multi-location": 5.0,
            "portal": 3.0,
            "online booking": 3.0,
            "online forms": 3.0,
            "telehealth": 3.0,
            "weekend": 4.0,
            "extended hours": 4.0,
            "review": 2.0,
            "growth": 4.0,
        }
        matched_signals: list[str] = []
        signal_bonus = 0.0
        for signal in signals:
            for keyword, weight in signal_keywords.items():
                if keyword in signal:
                    signal_bonus += weight
                    matched_signals.append(signal)
                    break

        if matched_signals:
            score += min(16.0, signal_bonus)
            reasons.append(f"Operating signals indicate active change pressure: {', '.join(matched_signals[:2])}.")

        if len(pain_hits) >= 2 and matched_signals:
            score += 6.0
            reasons.append("Pain-point density and live operating signals both suggest a strong workflow fit.")

        if clinic_type == "dental" and any(term in specialty for term in ("dentistry", "orthodontics", "pediatric dentistry")):
            score += 4.0
            reasons.append("Dental workflow profile aligns well with ClinicOS front-desk and recall automation use cases.")

        if existing_lead:
            score += 5.0
            reasons.append("Existing lead history lowers activation risk.")

        score = max(0.0, min(100.0, score))
        if not reasons:
            reasons.append("Limited public signals; medium confidence fit estimate.")

        return round(score, 1), reasons
