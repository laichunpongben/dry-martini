from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class Security(Base):
    __tablename__ = "securities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cusip = Column(String(12), unique=True, nullable=True)
    isin = Column(String(15), unique=True, nullable=True)
    sedol = Column(String(12), unique=True, nullable=True)

    # ← NEW RELATIONSHIP
    documents = relationship("Document", back_populates="security", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    security_id = Column(Integer, ForeignKey("securities.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String, nullable=False)
    url = Column(String, nullable=False)

    # ← BACK‐REFERENCE
    security = relationship("Security", back_populates="documents")
