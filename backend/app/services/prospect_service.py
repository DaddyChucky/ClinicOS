from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path


class ProspectService:
    SPECIALTY_PATTERNS: list[tuple[tuple[str, ...], str, str]] = [
        (("orthodont", "ortho"), "dental", "orthodontics"),
        (("pediatric dental", "kids dental"), "dental", "pediatric dentistry"),
        (("dental", "dentistry", "smile", "oral"), "dental", "family dentistry"),
        (("pediatr", "children"), "medical", "pediatrics"),
        (("women", "obgyn", "gyn", "ob"), "medical", "obgyn"),
        (("derm", "skin"), "medical", "dermatology"),
        (("urgent care",), "medical", "urgent care"),
    ]

    PROFILE_LIBRARY: dict[str, dict[str, list[str] | str]] = {
        "family dentistry": {
            "clinic_type": "dental",
            "size_options": ["4-8 providers", "6-12 providers", "3-5 providers"],
            "pain_points": [
                "manual recall reactivation for overdue hygiene patients",
                "insurance verification delays during the morning rush",
                "high front-desk call volume tied to scheduling changes",
                "treatment follow-up slipping between front desk and billing",
                "new patient intake packets slowing chair utilization",
            ],
            "signals": [
                "online booking and patient forms are highlighted on the website",
                "recent hiring activity for front office or treatment coordination",
                "expanded service mix suggests growing scheduling complexity",
                "multiple financing or insurance callouts point to revenue-cycle sensitivity",
                "review volume suggests active new-patient acquisition",
            ],
        },
        "orthodontics": {
            "clinic_type": "dental",
            "size_options": ["3-5 providers", "4-8 providers", "6-12 providers"],
            "pain_points": [
                "treatment plan follow-up and financing coordination lag",
                "manual rescheduling around consults, bonding, and adjustment visits",
                "recall and no-show recovery across active cases",
                "front-desk overload from consult conversion follow-up",
                "capacity planning friction across multiple chair types",
            ],
            "signals": [
                "before-and-after or smile gallery pages point to high lead velocity",
                "weekend or extended hours indicate throughput pressure",
                "consultation-heavy intake flow suggests follow-up orchestration needs",
                "patient financing language points to conversion-sensitive workflows",
                "multi-location or satellite wording suggests centralized operations demands",
            ],
        },
        "pediatric dentistry": {
            "clinic_type": "dental",
            "size_options": ["3-5 providers", "4-8 providers"],
            "pain_points": [
                "parent intake paperwork creates check-in bottlenecks",
                "recall reminders need better timing around family schedules",
                "front desk call spikes around school breaks and cancellations",
                "follow-up coordination for treatment plans and referrals is inconsistent",
                "insurance verification for family appointments adds manual overhead",
            ],
            "signals": [
                "school-season scheduling patterns suggest recall coordination pressure",
                "family-friendly new patient pages point to recurring intake volume",
                "same-day emergency language suggests volatile schedule management",
                "review activity indicates strong word-of-mouth growth",
                "expanded sedation or specialty services increase operational complexity",
            ],
        },
        "pediatrics": {
            "clinic_type": "medical",
            "size_options": ["6-12 providers", "10-20 providers", "8-15 providers"],
            "pain_points": [
                "long intake paperwork cycles for new families",
                "missed well-visit and vaccine follow-up workflows",
                "billing follow-up backlog after high-volume visits",
                "phone congestion during same-day appointment windows",
                "portal activation and reminder workflows are inconsistent",
            ],
            "signals": [
                "same-day sick visit messaging signals volatile schedule demand",
                "patient portal or online forms point to active digital operations",
                "career pages suggest expansion in front-office or operations roles",
                "multiple providers and family-focused services increase reminder complexity",
                "after-hours guidance pages point to elevated inbound message volume",
            ],
        },
        "obgyn": {
            "clinic_type": "medical",
            "size_options": ["8-15 providers", "10-20 providers", "6-12 providers"],
            "pain_points": [
                "follow-up coordination across prenatal, annual, and procedure visits",
                "prior authorization and billing handoff delays",
                "manual reminder workflows for recurring care plans",
                "front desk overload around referral and records requests",
                "new patient intake and consent workflows slowing check-in",
            ],
            "signals": [
                "telehealth or prenatal resource pages suggest multi-step care coordination",
                "provider expansion indicates growing scheduling complexity",
                "multiple service lines point to heavier authorization workflows",
                "career pages suggest active operations or revenue-cycle hiring",
                "patient education content suggests high recurring visit volume",
            ],
        },
        "dermatology": {
            "clinic_type": "medical",
            "size_options": ["4-8 providers", "6-12 providers", "8-15 providers"],
            "pain_points": [
                "cosmetic consult follow-up is inconsistent",
                "front desk load increases with high appointment turnover",
                "patient intake and photo/document collection remain manual",
                "recall and reactivation for recurring treatments is fragmented",
                "billing coordination across cosmetic and insurance visits adds friction",
            ],
            "signals": [
                "service pages suggest a mix of cosmetic and medical visit types",
                "online booking or cosmetic consult calls-to-action indicate lead volume",
                "before-and-after galleries suggest ongoing nurture and conversion workflows",
                "multi-provider rosters imply centralized schedule management needs",
                "reputation and review programs point to growth focus",
            ],
        },
        "urgent care": {
            "clinic_type": "medical",
            "size_options": ["10-20 providers", "8-15 providers", "6-12 providers"],
            "pain_points": [
                "registration and intake queues create front-desk congestion",
                "billing follow-up after walk-in volume is inconsistent",
                "post-visit follow-up and review requests are mostly manual",
                "staff handoff friction between intake and clinical teams",
                "records and referral coordination adds back-office drag",
            ],
            "signals": [
                "walk-in messaging indicates volatile same-day demand",
                "extended hours or weekend coverage suggests staffing coordination pressure",
                "multiple visit types create triage and registration complexity",
                "location pages or urgent access messaging imply volume growth",
                "online check-in or digital registration points to active workflow modernization",
            ],
        },
        "general practice": {
            "clinic_type": "medical",
            "size_options": ["6-12 providers", "8-15 providers", "4-8 providers"],
            "pain_points": [
                "new patient intake paperwork still creates bottlenecks",
                "follow-up reminder workflows vary by staff member",
                "billing follow-up and eligibility checks create back-office drag",
                "front-desk call volume spikes around schedule changes",
                "referral and records requests create manual coordination work",
            ],
            "signals": [
                "online forms or patient portal messaging suggests workflow modernization",
                "career pages indicate staffing or growth activity",
                "multi-provider rosters imply more complex scheduling coordination",
                "preventive and chronic-care mix suggests recurring recall needs",
                "expanded access messaging indicates throughput pressure",
            ],
        },
    }

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path(__file__).resolve().parent.parent / "data"
        self.mock_prospects = self._load_json("mock_prospects.json")

    def _load_json(self, filename: str) -> list[dict]:
        path = self.data_dir / filename
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _stable_index(self, seed: str, size: int) -> int:
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % max(size, 1)

    def _rotate_sample(self, options: list[str], seed: str, count: int) -> list[str]:
        if not options:
            return []

        start = self._stable_index(seed, len(options))
        ordered = options[start:] + options[:start]
        unique: list[str] = []
        for item in ordered:
            if item not in unique:
                unique.append(item)
            if len(unique) >= count:
                break
        return unique

    def _infer_profile_template(self, clinic_name: str) -> tuple[str, str]:
        normalized = clinic_name.strip().lower()
        for keywords, clinic_type, specialty in self.SPECIALTY_PATTERNS:
            if any(keyword in normalized for keyword in keywords):
                return clinic_type, specialty
        return "medical", "general practice"

    def _build_inferred_profile(self, clinic_name: str, location: str | None = None) -> dict:
        clinic_type, specialty = self._infer_profile_template(clinic_name)
        template = self.PROFILE_LIBRARY.get(specialty, self.PROFILE_LIBRARY["general practice"])
        seed = f"{clinic_name.strip().lower()}::{(location or '').strip().lower()}"
        name_lower = clinic_name.strip().lower()

        size_options = list(template["size_options"])
        if any(token in name_lower for token in ("group", "associates", "partners", "center", "centre")):
            size_estimate = size_options[min(len(size_options) - 1, 1)]
        else:
            size_estimate = size_options[self._stable_index(seed, len(size_options))]

        signals = self._rotate_sample(list(template["signals"]), seed, 3)
        if "location" in name_lower or "group" in name_lower:
            signals.append("brand language suggests multi-site or centralized operations oversight")
        if location:
            signals.append(f"location footprint in {location} suggests market-specific staffing and scheduling pressure")

        pain_points = self._rotate_sample(list(template["pain_points"]), f"{seed}::pain", 3)
        existing_lead = self._stable_index(f"{seed}::lead", 5) == 0

        return {
            "clinic_name": clinic_name,
            "clinic_type": str(template["clinic_type"]),
            "specialty": specialty,
            "size_estimate": size_estimate,
            "location": location or "Unknown",
            "existing_lead": existing_lead,
            "pain_points": pain_points,
            "signals": list(dict.fromkeys(signals))[:4],
        }

    def research_clinic(self, clinic_name: str, location: str | None = None) -> dict:
        normalized = clinic_name.strip().lower()
        candidate = None
        for record in self.mock_prospects:
            if record["clinic_name"].lower() == normalized:
                candidate = deepcopy(record)
                break

        if candidate is None:
            candidate = self._build_inferred_profile(clinic_name, location)

        if location and not candidate.get("location"):
            candidate["location"] = location
        return candidate
