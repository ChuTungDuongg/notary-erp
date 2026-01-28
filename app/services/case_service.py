from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from app.schemas.case import CaseCreate
from app.models.case import Case, CaseType
from app.models.party import Party
from app.models.case_party import CaseParty, PartyRole
from app.models.property import Property

def get_or_create_party(db: Session, *, cccd: str, **fields) -> Party:
    existing = db.execute(select(Party).where(Party.cccd == cccd)).scalar_one_or_none()
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        return existing

    p = Party(cccd=cccd, **fields)
    db.add(p)
    return p

def create_case(db: Session, payload : CaseCreate) -> Case:
    validate_case_payload(payload)
    case = Case(
        code=payload.code,
        case_type=CaseType[payload.case_type],  # expects enum name
        signing_date=payload.signing_date,
        transfer_price=payload.transfer_price,
    )

    case.property = Property(**payload.property.model_dump())

    for p in payload.parties:
        role = PartyRole[p.role]  # expects "SELLER"/"BUYER"
        party = get_or_create_party(
            db,
            cccd=p.cccd,
            full_name=p.full_name,
            cccd_issue_date=p.cccd_issue_date,
            cccd_issue_place=p.cccd_issue_place,
            address=p.address,
            phone=p.phone,
        )
        link = CaseParty(party = party, role = role)
        db.add(link)
        case.parties.append(link)

    db.add(case)
    db.commit()
    db.refresh(case)
    return case

def validate_case_payload(payload : CaseCreate) -> None:
    if payload.property is None:
        raise HTTPException(status_code=400, detail="properties is required!")
    
    if not payload.parties or len(payload.parties) == 0:
        raise HTTPException(status_code=400, detail="parties is required!")
    
    roles = [p.role for p in payload.parties]
    seller_count = sum(1 for r in roles if r == "SELLER")
    buyer_count = sum(1 for r in roles if r == "BUYER")

    if seller_count != 1 or buyer_count != 1:
        raise HTTPException(
            status_code=400,
            detail=f"require exactly 1 SELLER and 1 BUYER (got SELLER={seller_count}, BUYER={buyer_count})",
        )
    #cccd không được trùng trong payload 
    cccds = [p.cccd for p in payload.parties if p.cccd]
    if len(cccds) != len(set(cccds)):
        raise HTTPException(status_code=400, detail="duplicate cccd in parties")
    
    if payload.transfer_price is not None and payload.transfer_price < 0:
        raise HTTPException(status_code= 400, detail="transfer price must be higher > 0")
    

    

