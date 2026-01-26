from docx import Document as DocxDocument
from sqlalchemy.orm import Session
from app.models.case import Case
from app.models.document import Document as Document, DocumentType

def generate_contract(case: Case, session: Session) -> Document:
    doc = DocxDocument("templates/contract_transfer.docx")

    data = {
        "{{transfer_price}}" : str(case.transfer_price),
    }

    for p in case.parties:
        if p.role.name == "SELLER":
            data["{{seller_name}}"] = p.party.full_name
            data["{{seller_cccd}}"] = p.party.cccd or ""
        if p.role.name == "BUYER":
            data["{{buyer_name}}"] = p.party.full_name
            data["{{buyer_cccd}}"] = p.party.cccd or ""

    for para in doc.paragraphs:
        for k, v in data.items():
            if k in para.text:
                para.text = para.text.replace(k, v)

    file_path = f"data/file/{case.model}_contract_v1.docx"
    doc.save(file_path)

    record = Document(
        case = case,
        doc_type = DocumentType.CONTRACT_TRANSFER,
        version = 1,
        file_path = file_path
    )

    session.add(record)
    session.commit()

    return record
