# models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel, ConfigDict

# SQLAlchemy base
class Base(DeclarativeBase):
    pass

class Security(Base):
    __tablename__ = "securities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)              # renamed!
    cusip = Column(String(12), nullable=True)
    isin = Column(String(15), nullable=True, index=True, unique=True)
    sedol = Column(String(12), nullable=True)

# Pydantic schema
class SecuritySchema(BaseModel):
    id: int
    name: str                                        # renamed!
    cusip: str | None
    isin: str | None
    sedol: str | None

    model_config = ConfigDict(from_attributes=True)
