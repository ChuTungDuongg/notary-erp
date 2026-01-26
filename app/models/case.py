import enum
from datetime import datetime, date, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Date, Enum as SAEnum, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .case_party import CaseParty
    from .property import Property
    from .document import Document
    # sau này bạn sẽ thêm:
    # from .document import Document
    
class CaseType(str, enum.Enum):
    TRANSFER_LAND = "TRANSFER_LAND"
    
    
class Case(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(primary_key= True)
    
    code: Mapped[str] = mapped_column(String(32), unique= True, index = True)
    
    case_type : Mapped[CaseType] = mapped_column(SAEnum(CaseType), nullable= False, 
                                                 default = CaseType.TRANSFER_LAND)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, 
                                                 default= lambda: datetime.now(timezone.utc))
    
    signing_date : Mapped[date | None] = mapped_column(Date, nullable= True)
    
    parties: Mapped[list["CaseParty"]] = relationship(
        back_populates="case",
        cascade= "all, delete-orphan"
    )
    
    property: Mapped["Property | None"] = relationship(
        back_populates="case",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    documents: Mapped[list["Document"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan"
    )

    transfer_price : Mapped[float | None] = mapped_column(Numeric(18,2), nullable= True)
    