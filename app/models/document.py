import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Integer, DateTime, Enum as SAEnum, UniqueConstraint

from sqlalchemy.orm import Mapped, mapped_column, relationship

from.base import Base

if TYPE_CHECKING:
    from .case import Case

class DocumentType(str, enum.Enum):
    CONTRACT_TRANSFER = "CONTRACT_TRANSFER"
    OWNERSHIP_CERTIFICATE = "OWNERSHIP_CERTIFICATE"
    FEE_REGISTRATION = "FEE_REGISTRATION"

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("case_id", "doc_type", "version", name="uq_documents_case_type_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False, index=True)

    doc_type: Mapped[DocumentType] = mapped_column(SAEnum(DocumentType), nullable=False)

    version : Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    file_path : Mapped[str] = mapped_column(String(1000), nullable=False)

    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                  default=lambda: datetime.now(timezone.utc))
    
    case: Mapped["Case"] = relationship(back_populates="documents")