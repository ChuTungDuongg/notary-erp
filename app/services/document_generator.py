from docx import Document as DocxDocument
from sqlalchemy.orm import Session
from app.models.case import Case
from app.models.document import Document, DocumentType
from pathlib import Path
from sqlalchemy import select, func


def _replace_in_paragraph(paragraph, mapping: dict[str, str]) -> None:
    # Lưu ý: paragraph.text sẽ gộp runs; với template do python-docx tạo như bạn thì ổn.
    text = paragraph.text
    for k, v in mapping.items():
        if k in text:
            text = text.replace(k, v)
    if text != paragraph.text:
        paragraph.text = text

def _replace_everywhere(doc, mapping: dict[str, str]) -> None:
    for para in doc.paragraphs:
        _replace_in_paragraph(para, mapping)

    # Nếu docx có bảng (table) thì replace luôn trong cell
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    _replace_in_paragraph(para, mapping)

def generate_contract(case: Case, session: Session) -> Document:
    doc = DocxDocument("templates/contract_transfer.docx")

    # Tính version mới theo (case_id, doc_type)
    max_ver = session.execute(
        select(func.max(Document.version)).where(
            Document.case_id == case.id,
            Document.doc_type == DocumentType.CONTRACT_TRANSFER,
        )
    ).scalar_one()
    new_version = (max_ver or 0) + 1

    prop = case.property  # có thể None

    data = {
        "{{transfer_price}}": f"{case.transfer_price:,}".replace(",", ".") if case.transfer_price else "",
        "{{signing_date}}": str(case.signing_date) if case.signing_date else "",

        # property
        "{{property_address}}": prop.address if prop else "",
        "{{property_map_sheet_no}}": prop.map_sheet_no if prop else "",
        "{{property_parcel_no}}": prop.parcel_no if prop else "",
        "{{property_area_m2}}": str(prop.area_m2) if (prop and prop.area_m2 is not None) else "",
        "{{property_certificate_no}}": prop.certificate_no if prop else "",

        # default cho seller/buyer để khỏi sót placeholder
        "{{seller_name}}": "",
        "{{seller_cccd}}": "",
        "{{seller_address}}": "",
        "{{buyer_name}}": "",
        "{{buyer_cccd}}": "",
        "{{buyer_address}}": "",
    }

    for cp in case.parties:
        role = getattr(cp.role, "name", None)
        if role == "SELLER":
            data["{{seller_name}}"] = cp.party.full_name or ""
            data["{{seller_cccd}}"] = cp.party.cccd or ""
            data["{{seller_address}}"] = cp.party.address or ""
        elif role == "BUYER":
            data["{{buyer_name}}"] = cp.party.full_name or ""
            data["{{buyer_cccd}}"] = cp.party.cccd or ""
            data["{{buyer_address}}"] = cp.party.address or ""

    _replace_everywhere(doc, data)

    file_path = f"data/files/{case.code}_contract_v{new_version}.docx"
    out_path = Path(file_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(file_path)

    record = Document(
        case=case,
        doc_type=DocumentType.CONTRACT_TRANSFER,
        version=new_version,
        file_path=file_path,
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    return record
