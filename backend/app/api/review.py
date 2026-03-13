from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import ReviewQueueItem
from app.repositories.draft_repository import DraftRepository

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/queue", response_model=list[ReviewQueueItem])
def review_queue(db: Session = Depends(get_db)):
    repo = DraftRepository(db)
    return repo.get_review_queue()
