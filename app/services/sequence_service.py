from __future__ import annotations
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.sequences import DailySequence

def next_case_code(db: Session, *, prefix : str = "HS", d : date | None = None) -> str:
    d = d or date.today()
    day = d.strftime("%Y%m%d")

    seq = db.execute(select(DailySequence).where(DailySequence.day == day)).scalar_one_or_none()

    if seq is None:
        seq = DailySequence(day = day, last_int = 0)
        db.add(seq)
        db.flush()

    seq.last_int = seq.last_int + 1
    db.flush()

    return f"{prefix}-{day}-{seq.last_int:04d}"