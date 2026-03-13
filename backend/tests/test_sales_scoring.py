from __future__ import annotations

from app.services.prospect_service import ProspectService
from app.services.scoring_service import ScoringService
from app.tools.sales_tools import build_outreach_draft


def test_sales_scoring_returns_valid_range_and_reasons():
    service = ScoringService()
    score, reasons = service.score_icp_fit(
        {
            "clinic_type": "dental",
            "specialty": "family dentistry",
            "size_estimate": "4-8 providers",
            "pain_points": ["manual recall reminders", "billing follow-up backlog"],
            "signals": ["recent hiring activity for front office or treatment coordination"],
            "existing_lead": True,
        }
    )

    assert 0 <= score <= 100
    assert score >= 70
    assert len(reasons) > 0


def test_prospect_service_infers_specialty_and_varies_unknown_profiles():
    service = ProspectService()

    dental = service.research_clinic("Harbor Kids Dental", "Portland, OR")
    ortho = service.research_clinic("Summit Ortho Group", "Denver, CO")

    assert dental["clinic_type"] == "dental"
    assert dental["specialty"] == "pediatric dentistry"
    assert "manual intake paperwork" not in dental["pain_points"]
    assert any("school" in signal or "family" in signal for signal in dental["signals"])
    assert ortho["specialty"] == "orthodontics"
    assert dental["pain_points"] != ortho["pain_points"]


def test_outreach_draft_uses_dynamic_signals_and_pains():
    draft = build_outreach_draft(
        {
            "clinic_name": "Summit Ortho Group",
            "specialty": "orthodontics",
            "location": "Denver, CO",
            "pain_points": [
                "treatment plan follow-up and financing coordination lag",
                "manual rescheduling around consults, bonding, and adjustment visits",
            ],
            "signals": [
                "weekend or extended hours indicate throughput pressure",
                "patient financing language points to conversion-sensitive workflows",
            ],
        },
        84,
        [
            "Operating signals indicate active change pressure: weekend or extended hours indicate throughput pressure.",
            "Pain-point density and live operating signals both suggest a strong workflow fit.",
        ],
    )

    assert "weekend or extended hours indicate throughput pressure" in draft["body"].lower()
    assert "manual rescheduling around consults" in draft["body"].lower()
    assert "weekend or extended hours indicate throughput pressure" in draft["personalization_notes"].lower()
