from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .case import Case
    
class Property(Base):
    __tablename__ = "properties"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id"),
        nullable= False,
        unique= True,
        index= True
    )
    
    address: Mapped[str | None] = mapped_column(String(500), nullable= True)
    map_sheet_no : Mapped[str | None] = mapped_column(String(50), nullable= True) #tờ bản đồ
    parcel_no: Mapped[str | None] = mapped_column(String(50), nullable= True) # thửa
    area_m2: Mapped[float | None] = mapped_column(Numeric(18,2), nullable= True)
    certificate_no : Mapped[str | None] = mapped_column(String(100), nullable= True)
    
    case: Mapped["Case"] = relationship(back_populates="property")