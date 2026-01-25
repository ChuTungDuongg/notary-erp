import enum
from sqlalchemy import Integer, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .case import Case
    from .party import Party

class PartyRole(str, enum.Enum):
    SELLER = "SELLER"
    BUYER = "BUYER"
    
class CaseParty(Base):
    __tablename__ = "case_parties"
    
    __table_args__ = (
        UniqueConstraint('case_id', 'party_id', 'role', name='uq_case_party_role'),
    )
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False, index = True)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id"), nullable=False, index = True)

    role: Mapped[PartyRole] = mapped_column(SAEnum(PartyRole), nullable=False)
    
    case: Mapped["Case"] = relationship(back_populates="parties")
    party: Mapped["Party"] = relationship(back_populates="case_links")
