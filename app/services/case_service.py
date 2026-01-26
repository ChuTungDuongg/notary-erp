from sqlalchemy.orm import Session
from sqlalchemy import select

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
        case.parties.append(CaseParty(party=party, role=role))

    db.add(case)
    db.commit()
    db.refresh(case)
    return case