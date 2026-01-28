from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from app.db import get_db

from app.models.case import Case
from app.models.document import Document, DocumentType

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


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    parties_out = []
    for cp in case.parties or []:
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
