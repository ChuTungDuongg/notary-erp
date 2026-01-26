from pydantic import BaseModel

class DocumentOut(BaseModel):
    id: int
    case_id: int
    doc_type: str
    version: int
    file_path: str

    class Config:
        from_attributes = True
