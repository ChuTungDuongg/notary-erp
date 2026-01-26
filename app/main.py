from fastapi import FastAPI, Depends
from pathlib import Path
from contextlib import asynccontextmanager
from app.db import init_db, get_db
from sqlalchemy.orm import Session
from app.schemas.case import CaseCreate, CaseOut
from app.services.case_service import create_case

from app.models.case import Case
from app.models.document import Document
from app.schemas.document import DocumentOut
from app.services.document_generator import generate_contract
from fastapi import HTTPException

from fastapi.responses import FileResponse
from pathlib import Path

from typing import List
from sqlalchemy import select
from app.schemas.case import CaseListItem
from app.models.case import Case
from app.schemas.case import CaseDetail, PartyOut, PropertyOut

from app.models.document import Document
from app.schemas.document import DocumentOut

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

@app.post("/cases/{case_id}/generate-contract", response_model=DocumentOut)
def api_generate_contract(case_id: int, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if not case.property:
        raise HTTPException(status_code=400, detail="Case has no property")
    if not case.parties:
        raise HTTPException(status_code=400, detail="Case has no parties")

    doc = generate_contract(case, db)
    return doc


@app.get("/documents/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    path = Path(doc.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")

    return FileResponse(
        str(path),
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

@app.get("/cases", response_model=List[CaseListItem])
def list_cases(db: Session = Depends(get_db)):
    rows = db.execute(select(Case).order_by(Case.id.desc())).scalars().all()
    return rows

@app.get("/cases/{case_id}", response_model=CaseDetail)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    parties_out = []
    for cp in case.parties:  # cp: CaseParty
        parties_out.append(
            PartyOut(
                id=cp.party.id,
                full_name=cp.party.full_name,
                cccd=cp.party.cccd,
                address=cp.party.address,
                phone=cp.party.phone,
                role=cp.role.name,
            )
        )

    prop_out = None
    if case.property:
        prop = case.property
        prop_out = PropertyOut(
            id=prop.id,
            address=prop.address,
            map_sheet_no=prop.map_sheet_no,
            parcel_no=prop.parcel_no,
            area_m2=prop.area_m2,
            certificate_no=prop.certificate_no,
        )

    return CaseDetail(
        id=case.id,
        code=case.code,
        case_type=case.case_type.name if hasattr(case.case_type, "name") else str(case.case_type),
        signing_date=case.signing_date,
        transfer_price=case.transfer_price,
        property=prop_out,
        parties=parties_out,
    )

@app.get("/cases/{case_id}/documents", response_model=list[DocumentOut])
def list_case_documents(case_id: int, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    docs = (
        db.execute(select(Document).where(Document.case_id == case_id).order_by(Document.id.desc()))
        .scalars()
        .all()
    )
    return docs

