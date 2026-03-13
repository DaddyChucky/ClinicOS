from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import db_models


class ProspectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, clinic_name: str) -> db_models.Prospect | None:
        stmt = select(db_models.Prospect).where(
            func.lower(db_models.Prospect.clinic_name) == clinic_name.strip().lower()
        )
        return self.db.scalar(stmt)

    def create_or_update(
        self,
        clinic_name: str,
        clinic_type: str,
        conversation_id: int | None = None,
        specialty: str | None = None,
        size_estimate: str | None = None,
        location: str | None = None,
        existing_lead: bool = False,
        fit_score: float | None = None,
        pain_points: list[str] | None = None,
        research_summary: str | None = None,
    ) -> db_models.Prospect:
        prospect = self.get_by_name(clinic_name)
        if prospect:
            prospect.conversation_id = conversation_id or prospect.conversation_id
            prospect.clinic_type = clinic_type
            prospect.specialty = specialty
            prospect.size_estimate = size_estimate
            prospect.location = location
            prospect.existing_lead = existing_lead
            prospect.fit_score = fit_score
            prospect.pain_points_json = pain_points
            prospect.research_summary = research_summary
        else:
            prospect = db_models.Prospect(
                conversation_id=conversation_id,
                clinic_name=clinic_name,
                clinic_type=clinic_type,
                specialty=specialty,
                size_estimate=size_estimate,
                location=location,
                existing_lead=existing_lead,
                fit_score=fit_score,
                pain_points_json=pain_points,
                research_summary=research_summary,
            )
            self.db.add(prospect)

        self.db.commit()
        self.db.refresh(prospect)
        return prospect

    def get(self, prospect_id: int) -> db_models.Prospect | None:
        return self.db.get(db_models.Prospect, prospect_id)

    def list_all(self) -> list[db_models.Prospect]:
        stmt = select(db_models.Prospect).order_by(db_models.Prospect.updated_at.desc())
        return list(self.db.scalars(stmt).all())
