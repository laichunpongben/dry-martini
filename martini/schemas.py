# schemas.py

from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class DocumentSchema(BaseModel):
    id: int
    doc_type: str
    url: str

    # enable .from_orm() / ORM-style parsing
    model_config = ConfigDict(from_attributes=True)

class SecuritySchema(BaseModel):
    id: int
    name: str
    cusip: Optional[str]
    isin: Optional[str]
    sedol: Optional[str]

    # ← NESTED DOCUMENTS
    documents: List[DocumentSchema] = []

    # enable .from_orm() / ORM-style parsing
    model_config = ConfigDict(from_attributes=True)

class DocumentCreate(BaseModel):
    doc_type: str
    url: str
