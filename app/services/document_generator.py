from __future__ import annotations

from pathlib import Path
from typing import Dict

from docx import Document as DocxDocument
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.document import Document, DocumentType


def _replace_in_paragraph(paragraph, mapping: Dict[str, str]) -> None:
    """
    Replace placeholders while keeping template formatting as much as possible.
    - Prefer run-level replace (keeps font/style).
    - Fallback: if placeholder spans runs, do a safe paragraph-level rebuild
      (may affect mixed formatting in that paragraph).
    """
    # 1) run-level replace (preserve formatting)
    hit = False
    for run in paragraph.runs:
        if not run.text:
            continue
        new_text = run.text
        for k, v in mapping.items():
            if k in new_text:
                new_text = new_text.replace(k, v)
        if new_text != run.text:
            run.text = new_text
            hit = True

    # 2) fallback if placeholders span multiple runs
    # (e.g. "{{seller_name}}" bị tách thành nhiều run)
    if not hit:
        full = paragraph.text
        new_full = full
        for k, v in mapping.items():
            if k in new_full:
                new_full = new_full.replace(k, v)

        if new_full != full:
            # rebuild paragraph text: keep first run formatting if exists
            if paragraph.runs:
                paragraph.runs[0].text = new_full
                for r in paragraph.runs[1:]:
                    r.text = ""
            else:
                paragraph.add_run(new_full)


def _replace_everywhere(doc, mapping: Dict[str, str]) -> None:
    for para in doc.paragraphs:
        _replace_in_paragraph(para, mapping)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    _replace_in_paragraph(para, mapping)


def generate_contract(case: Case, db: Session) -> Document:
    """
    Generate a new contract docx from template, create a Document record with auto-incremented version.
    IMPORTANT: do NOT commit here. Caller should commit.
    """
    doc = DocxDocument("templates/contract_transfer.docx")

    # 1) next version by (case_id, doc_type)
    max_ver = db.execute(
        select(func.max(Document.version)).where(
            Document.case_id == case.id,
            Document.doc_type == DocumentType.CONTRACT_TRANSFER,
        )
    ).scalar_one()
    new_version = (max_ver or 0) + 1

    prop = case.property  # can be None

    # 2) build mapping
    data: Dict[str, str] = {
        "{{transfer_price}}": f"{case.transfer_price:,}".replace(",", ".") if case.transfer_price else "",
        "{{signing_date}}": str(case.signing_date) if case.signing_date else "",

        "{{property_address}}": prop.address if prop else "",
        "{{property_map_sheet_no}}": prop.map_sheet_no if prop else "",
        "{{property_parcel_no}}": prop.parcel_no if prop else "",
        "{{property_area_m2}}": str(prop.area_m2) if (prop and prop.area_m2 is not None) else "",
        "{{property_certificate_no}}": prop.certificate_no if prop else "",

        "{{seller_name}}": "",
        "{{seller_cccd}}": "",
        "{{seller_address}}": "",
        "{{buyer_name}}": "",
        "{{buyer_cccd}}": "",
        "{{buyer_address}}": "",
    }

    for cp in (case.parties or []):
        role = getattr(cp.role, "name", None)
        if role == "SELLER":
            data["{{seller_name}}"] = cp.party.full_name or ""
            data["{{seller_cccd}}"] = cp.party.cccd or ""
            data["{{seller_address}}"] = cp.party.address or ""
        elif role == "BUYER":
            data["{{buyer_name}}"] = cp.party.full_name or ""
            data["{{buyer_cccd}}"] = cp.party.cccd or ""
            data["{{buyer_address}}"] = cp.party.address or ""

    # 3) replace
    _replace_everywhere(doc, data)

    # 4) output path (folder per case)
    out_dir = Path("data/files") / case.code
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"contract_v{new_version}.docx"
    doc.save(str(out_path))

    # 5) db record (no commit here)
    record = Document(
        case_id=case.id,
        doc_type=DocumentType.CONTRACT_TRANSFER,
        version=new_version,
        file_path=str(out_path),
    )
    db.add(record)
    db.flush()
    db.refresh(record)
    return record
