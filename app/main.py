from fastapi import FastAPI, Depends
from pathlib import Path
from contextlib import asynccontextmanager
from app.db import init_db, get_db
from sqlalchemy.orm import Session
from app.schemas.case import CaseCreate, CaseOut
from app.services.case_service import create_case


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    init_db()
    Path("data/files").mkdir(parents=True, exist_ok=True)
    yield
    # shutdown (sau này cần thì thêm)

app = FastAPI(
    title="Notary ERP",
    lifespan=lifespan,
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/cases", response_model=CaseOut)
def api_create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    case = create_case(db, payload)
    return case