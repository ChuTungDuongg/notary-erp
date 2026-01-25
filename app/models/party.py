from typing import TYPE_CHECKING
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Date
from datetime import date
if TYPE_CHECKING:
    from .case_party import CaseParty

class Party(Base):
    __tablename__ = "parties"
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    
    full_name : Mapped[str] = mapped_column(String(255), nullable=False)
    cccd : Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    
    cccd_issue_date : Mapped[date] = mapped_column(Date, nullable=False)
    cccd_issue_place : Mapped[str] = mapped_column(String(255), nullable=False)
    
    address : Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone : Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    case_links : Mapped[list["CaseParty"]] = relationship(back_populates="party")
    