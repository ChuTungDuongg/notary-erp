from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.base import Base

from app.models.case import *
from app.models.party import *
from app.models.case_party import *
from app.models.property import *
from app.models.document import Document

from app.services.document_generator import generate_contract

DB_PATH = Path("notary_erp.db")
DB_URL = "sqlite:///notary_erp.db"

def get_or_create_party(session, **kwargs):
    cccd = kwargs.get("cccd")
    if cccd:
        existing = session.execute(
            select(Party).where(Party.cccd == cccd)
        ).scalar_one_or_none()
        if existing:
            # nếu muốn cập nhật lại thông tin thì update luôn
            for k, v in kwargs.items():
                setattr(existing, k, v)
            return existing

    p = Party(**kwargs)
    session.add(p)
    return p


def main():
    Path("data/files").mkdir(parents=True, exist_ok= True)

    engine = create_engine(DB_URL, future = True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind = engine, future = True)
    with SessionLocal() as session:
        case = Case(
            code = "CA-TEST-001",
            case_type = CaseType.TRANSFER_LAND,
            signing_date = None,
            transfer_price = 600_000_000,
        )
        
        seller = get_or_create_party(
            session,
            full_name="Nguyen Van A",
            cccd="012345678901",
            cccd_issue_date=date(2020, 1, 1),
            cccd_issue_place="CA TP HCM",
            address="Q1, HCM",
            phone="0909xxxxxx",
        )

        buyer = get_or_create_party(
            session,
            full_name="Tran Thi B",
            cccd="098765432109",
            cccd_issue_date=date(2020, 1, 1),
            cccd_issue_place="CA TP HCM",
            address="Q3, HCM",
            phone="0912xxxxxx",
        )


        link_seller = CaseParty(party = seller, role = PartyRole.SELLER)
        link_buyer = CaseParty(party = buyer, role = PartyRole.BUYER)

        case.parties.append(link_seller)
        case.parties.append(link_buyer)

        prop = Property(
            address = "123 Nguyen Trai, Q1, HCM",
            map_sheet_no = "12",
            parcel_no = "34",
            area_m2 = 80.5,
            certificate_no = "GCN - ABC - 123",
        )
        case.property = prop

        session.add(case)
        session.commit()

        case_id = case.id
        case = session.get(Case, case_id)

        doc_record = generate_contract(case, session)

        print("Generated document record:")
        print(" -id", doc_record.id)
        print(" -file path:", doc_record.file_path)

        rows = session.execute(select(Document).where(Document.case_id == case.id)).scalars().all()

        print("Documents in DB for case", case.code, ":", len(rows))
        for d in rows:
            print(" -", d.id, d.doc_type, d.version, d.file_path)
        out_path = Path(doc_record.file_path)
        print("File exists:", out_path.exists(), "|", out_path.resolve())

if __name__ == "__main__":
    main()