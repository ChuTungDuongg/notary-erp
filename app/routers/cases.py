from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from datetime import date
from typing import List, Optional

from app.db import get_db
from app.models.case import Case, CaseType
from app.models.property import Property
from app.models.case_party import CaseParty
from app.models.party import Party
from app.schemas.case import CaseListItem
from app.models.document import DocumentType

from app.schemas.case import (
    CaseCreate,
    CaseOut,
    CaseListItem,
    CaseDetail,
    PartyOut,
    PropertyOut,
)
from app.schemas.document import DocumentOut

from app.services.case_service import create_case
from app.services.document_generator import generate_contract


router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseOut)
def api_create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    return create_case(db, payload)


@router.get("", response_model=List[CaseListItem])
def list_cases(db: Session = Depends(get_db)):
    rows = db.execute(select(Case).order_by(Case.id.desc())).scalars().all()
    return rows


@router.post("/{case_id}/generate-contract", response_model=DocumentOut)
def api_generate_contract(case_id: int, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if not case.property:
        raise HTTPException(status_code=400, detail="Case has no property")

    roles = [getattr(cp.role, "name", None) for cp in (case.parties or [])]
    seller_count = sum(1 for r in roles if r == "SELLER")
    buyer_count = sum(1 for r in roles if r == "BUYER")
    if seller_count != 1 or buyer_count != 1:
        raise HTTPException(
            status_code=400,
            detail=f"Case must have exactly 1 SELLER and 1 BUYER (got SELLER={seller_count}, BUYER={buyer_count})",
        )

    doc = generate_contract(case, db)
    return doc


@router.get("/{case_id}/documents", response_model=list[DocumentOut])
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


@router.get("/{case_id}/documents/latest", response_model=DocumentOut)
def get_latest_document(
    case_id: int,
    doc_type: DocumentType = Query(DocumentType.CONTRACT_TRANSFER),
    db: Session = Depends(get_db),
):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    latest = db.execute(
        select(Document)
        .where(Document.case_id == case_id, Document.doc_type == doc_type)
        .order_by(Document.version.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not latest:
        raise HTTPException(status_code=404, detail="No document for this case/doc_type")

    return latest

@router.get("/search", response_model=List[CaseListItem])
def search_cases(
    db: Session = Depends(get_db),

    # search chung
    q: Optional[str] = Query(None, description="Search: code/cccd/name/address"),

    # filter cụ thể
    id: Optional[int] = Query(None),
    case_type: Optional[CaseType] = Query(None),  # Swagger sẽ show đúng enum
    code: Optional[str] = Query(None),
    cccd: Optional[str] = Query(None),
    party_name: Optional[str] = Query(None),
    property_address: Optional[str] = Query(None),
    signing_from: Optional[date] = Query(None),
    signing_to: Optional[date] = Query(None),

    # paging
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    stmt = select(Case).order_by(Case.id.desc())

    # =========
    # 1) FILTER CỨNG (AND) - không join cũng lọc được
    # =========
    if id is not None:
        stmt = stmt.where(Case.id == id)
    
    if case_type is not None:
        stmt = stmt.where(Case.case_type == case_type)

    if code:
        stmt = stmt.where(Case.code.ilike(f"%{code}%"))

    if signing_from:
        stmt = stmt.where(Case.signing_date >= signing_from)

    if signing_to:
        stmt = stmt.where(Case.signing_date <= signing_to)

    # =========
    # 2) JOIN khi cần search/filter theo party/property
    # =========
    need_party = any([q, cccd, party_name])
    need_prop = any([q, property_address])

    if need_party:
        stmt = stmt.join(CaseParty, CaseParty.case_id == Case.id).join(Party, Party.id == CaseParty.party_id)

    if need_prop:
        stmt = stmt.join(Property, Property.case_id == Case.id)

    # =========
    # 3) FILTER theo bảng join (AND)
    # =========
    if cccd:
        stmt = stmt.where(Party.cccd.ilike(f"%{cccd}%"))

    if party_name:
        stmt = stmt.where(Party.full_name.ilike(f"%{party_name}%"))

    if property_address:
        stmt = stmt.where(Property.address.ilike(f"%{property_address}%"))

    # =========
    # 4) SEARCH CHUNG (OR) - chỉ dành cho q
    # =========
    if q:
        stmt = stmt.where(
            or_(
                Case.code.ilike(f"%{q}%"),
                Party.cccd.ilike(f"%{q}%") if need_party else False,
                Party.full_name.ilike(f"%{q}%") if need_party else False,
                Property.address.ilike(f"%{q}%") if need_prop else False,
            )
        )

    # =========
    # 5) DISTINCT để tránh duplicate Case khi join
    # =========
    if need_party or need_prop:
        stmt = stmt.distinct(Case.id)

    offset = (page - 1) * page_size
    rows = db.execute(stmt.offset(offset).limit(page_size)).scalars().all()
    return rows