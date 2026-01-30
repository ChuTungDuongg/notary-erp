from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from app.schemas.case import CaseCreate, CaseUpdate
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
    
def validate_parties_payload(parties) -> None:
    if not parties or len(parties) == 0:
        raise HTTPException(status_code=400, detail="parties is required!")

    roles = [p.role for p in parties]
    seller_count = sum(1 for r in roles if r == "SELLER")
    buyer_count = sum(1 for r in roles if r == "BUYER")
    if seller_count != 1 or buyer_count != 1:
        raise HTTPException(
            status_code=400,
            detail=f"require exactly 1 SELLER and 1 BUYER (got SELLER={seller_count}, BUYER={buyer_count})",
        )

    cccds = [p.cccd for p in parties if p.cccd]
    if len(cccds) != len(set(cccds)):
        raise HTTPException(status_code=400, detail="duplicate cccd in parties")


def update_case(db: Session, case_id: int, payload: CaseUpdate) -> Case:
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        # --- update field đơn giản ---
        if payload.signing_date is not None:
            case.signing_date = payload.signing_date

        if payload.transfer_price is not None:
            if payload.transfer_price < 0:
                raise HTTPException(status_code=400, detail="transfer price must be higher > 0")
            case.transfer_price = payload.transfer_price

        if payload.case_type is not None:
            try:
                case.case_type = CaseType[payload.case_type]
            except KeyError:
                try:
                    case.case_type = CaseType(payload.case_type)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"invalid case_type: {payload.case_type}")

        # --- property ---
        if payload.property is not None:
            if case.property:
                for k, v in payload.property.model_dump().items():
                    setattr(case.property, k, v)
            else:
                case.property = Property(**payload.property.model_dump())

        # --- parties ---
        if payload.parties is not None:
            validate_parties_payload(payload.parties)

            case.parties.clear()
            db.flush()

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
                case.parties.append(CaseParty(party=party, role=role))

        db.flush()
        db.commit()        # ✅ commit ở đây
        db.refresh(case)
        return case

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


    

