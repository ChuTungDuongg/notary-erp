from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class PartyIn(BaseModel):
    full_name : str
    cccd : str
    cccd_issue_date : Optional[date] = None
    cccd_issue_place : Optional[str] = None
    address : Optional[str] = None
    phone : Optional[str] = None
    role : str # SELLER or BUYER
    
class PropertyIn(BaseModel):
    address : str
    map_sheet_no : str
    parcel_no : str
    area_m2 : float
    certificate_no : str
    
class CaseCreate(BaseModel):
    code: str
    case_type: str  # ví dụ "TRANSFER_LAND"
    signing_date: Optional[date] = None
    transfer_price: Optional[int] = None

    parties: List[PartyIn]
    property: PropertyIn

class CaseOut(BaseModel):
    id: int
    code: str

    class Config:
        from_attributes = True