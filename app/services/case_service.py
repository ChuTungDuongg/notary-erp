from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from app.schemas.case import CaseCreate
from app.models.case import Case, CaseType
from app.models.party import Party
from app.models.case_party import CaseParty, PartyRole
from app.models.property import Property

from app.services.sequence_service import next_case_code

CASE_CODE_PREFIX_MAP = {
    "TRANSFER_LAND": "CN",
    "AUTHORIZATION": "UQ",
}



def get_or_create_party(db: Session, *, cccd: str, **fields) -> Party:
    existing = db.execute(select(Party).where(Party.cccd == cccd)).scalar_one_or_none()
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        return existing

    p = Party(cccd=cccd, **fields)
    db.add(p)
    return p

def create_case(db: Session, payload: CaseCreate) -> Case:
    validate_case_payload(payload)

    try:
        with db.begin():
            # prefix theo case_type (input đang là string)
            prefix = CASE_CODE_PREFIX_MAP.get(payload.case_type, "HS")

            # code: nếu client gửi thì check trùng, không thì generate
            if payload.code:
                existed = db.execute(
                    select(Case.id).where(Case.code == payload.code)
                ).scalar_one_or_none()
                if existed:
                    raise HTTPException(status_code=409, detail="case code already exists")
                code = payload.code
            else:
                code = next_case_code(db, prefix=prefix, d=payload.signing_date)

            # parse CaseType (vì model CaseType của bạn là TRANSFER_LAND)
            try:
                case_type = CaseType[payload.case_type]
            except KeyError:
                try:
                    case_type = CaseType(payload.case_type)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"invalid case_type: {payload.case_type}")

            case = Case(
                code=code,
                case_type=case_type,
                signing_date=payload.signing_date,
                transfer_price=payload.transfer_price,
            )

            case.property = Property(**payload.property.model_dump())

            # QUAN TRỌNG: add case trước + flush để case có id và nằm trong session
            db.add(case)
            db.flush()

            # QUAN TRỌNG: chặn autoflush khi đang query get_or_create_party
            for p in payload.parties:
                role = PartyRole[p.role]

                with db.no_autoflush:
                    party = get_or_create_party(
                        db,
                        cccd=p.cccd,
                        full_name=p.full_name,
                        cccd_issue_date=p.cccd_issue_date,
                        cccd_issue_place=p.cccd_issue_place,
                        address=p.address,
                        phone=p.phone,
                    )

                # chỉ cần append, cascade sẽ tự add link
                link = CaseParty(party=party, role=role)
                case.parties.append(link)

            db.flush()

        db.refresh(case)
        return case

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

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
    

    

