from pydantic import BaseModel
from typing import List

class DocumentSchema(BaseModel):
    id: int
    doc_type: str
    url: str

    class Config:
        orm_mode = True

class SecuritySchema(BaseModel):
    id: int
    name: str
    cusip: str | None
    isin: str | None
    sedol: str | None

    # ← NESTED DOCUMENTS
    documents: List[DocumentSchema] = []

    class Config:
        orm_mode = True

class DocumentCreate(BaseModel):
    doc_type: str
    url: str
