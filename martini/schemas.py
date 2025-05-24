# schemas.py

from datetime import date
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class DocumentSchema(BaseModel):
    id: int
    doc_type: str
    url: str

    model_config = ConfigDict(from_attributes=True)

class PriceHistorySchema(BaseModel):
    date: date
    open: float
    close: float
    high: float
    low: float
    volume: Optional[int]
    volume_nominal: Optional[int]

    model_config = ConfigDict(from_attributes=True)

class SecuritySchema(BaseModel):
    id: int
    name: str
    cusip: Optional[str]
    isin: Optional[str]
    sedol: Optional[str]
    documents: List[DocumentSchema] = []
    price_history: List[PriceHistorySchema] = []

    model_config = ConfigDict(from_attributes=True)

class DocumentCreate(BaseModel):
    doc_type: str
    url: str

class SecurityListItemSchema(BaseModel):
    isin: Optional[str]
    name: str

    model_config = ConfigDict(from_attributes=True)
