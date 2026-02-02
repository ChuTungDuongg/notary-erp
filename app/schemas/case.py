from pydantic import BaseModel
from datetime import date
from typing import Optional, List
from app.models.case import CaseStatus

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
    code: Optional[str] = None
    case_type: str  # ví dụ "TRANSFER_LAND"
    signing_date: Optional[date] = None
    transfer_price: Optional[int] = None

    parties: List[PartyIn]
    property: PropertyIn

class CaseOut(BaseModel):
    id: int
    code: str
    status: CaseStatus
    class Config:
        from_attributes = True
        
class CaseListItem(BaseModel):
    id: int
    code: str
    case_type: str
    signing_date: Optional[date] = None
    transfer_price: Optional[int] = None
    status: CaseStatus

    class Config:
        from_attributes = True
        
class PartyOut(BaseModel):
    id: int
    full_name: str
    cccd: str
    address: Optional[str] = None
    phone: Optional[str] = None
    role: str

    class Config:
        from_attributes = True

class PropertyOut(BaseModel):
    id: int
    address: str
    map_sheet_no: str
    parcel_no: str
    area_m2: float
    certificate_no: str

    class Config:
        from_attributes = True

class CaseDetail(BaseModel):
    id: int
    code: str
    case_type: str
    signing_date: Optional[date] = None
    transfer_price: Optional[int] = None
    property: Optional[PropertyOut] = None
    parties: List[PartyOut] = []
    status : CaseStatus

    class Config:
        from_attributes = True
        
class PropertyUpsert(BaseModel):
    address: str
    map_sheet_no: str
    parcel_no: str
    area_m2: float
    certificate_no: str

class PartyUpsert(BaseModel):
    role: str  # "SELLER" / "BUYER"
    cccd: str
    full_name: str
    cccd_issue_date: Optional[date] = None
    cccd_issue_place: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

class CaseUpdate(BaseModel):
    case_type: Optional[str] = None
    signing_date: Optional[date] = None
    transfer_price: Optional[float] = None
    property: Optional[PropertyUpsert] = None
    parties: Optional[List[PartyUpsert]] = None

class CaseStatusUpdate(BaseModel):
    status: CaseStatus