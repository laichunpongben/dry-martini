from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Date, Numeric
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from .db import Base

class Security(Base):
    __tablename__ = "securities"

    id     = Column(Integer, primary_key=True, index=True)
    name   = Column(String, nullable=False)
    cusip  = Column(String(12), unique=True, nullable=True)
    isin   = Column(String(15), unique=True, nullable=True)
    sedol  = Column(String(12), unique=True, nullable=True)

    documents     = relationship(
        "Document",
        back_populates="security",
        cascade="all, delete-orphan"
    )
    price_history = relationship(
        "PriceHistory",
        back_populates="security",
        order_by="PriceHistory.date",
        cascade="all, delete-orphan"
    )
    fund_holdings = relationship(
        "FundHolding",
        back_populates="security",
        cascade="all, delete-orphan"
    )

class Document(Base):
    __tablename__ = "documents"

    id          = Column(Integer, primary_key=True, index=True)
    security_id = Column(
        Integer,
        ForeignKey("securities.id", ondelete="CASCADE"),
        nullable=False
    )
    doc_type = Column(String, nullable=False)
    url      = Column(String, nullable=False)

    security = relationship("Security", back_populates="documents")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id             = Column(Integer, primary_key=True, index=True)
    security_id    = Column(
        Integer,
        ForeignKey("securities.id", ondelete="CASCADE"),
        nullable=False
    )
    date           = Column(Date, nullable=False)
    open           = Column(Numeric(12, 6), nullable=False)
    close          = Column(Numeric(12, 6), nullable=False)
    high           = Column(Numeric(12, 6), nullable=False)
    low            = Column(Numeric(12, 6), nullable=False)
    volume         = Column(Integer, nullable=True)
    volume_nominal = Column(Integer, nullable=True)

    security = relationship("Security", back_populates="price_history")

class AccessLog(Base):
    __tablename__ = "access_logs"

    id           = Column(Integer, primary_key=True, index=True)
    security_id  = Column(
        Integer,
        ForeignKey("securities.id", ondelete="CASCADE"),
        nullable=False
    )
    accessed_at  = Column(DateTime(timezone=True), nullable=False)
    client_ip    = Column(INET, nullable=True)
    user_agent   = Column(String, nullable=True)

    security = relationship("Security")

class Fund(Base):
    __tablename__ = "funds"

    id          = Column(Integer, primary_key=True, index=True)
    fund_name   = Column(String, nullable=False)
    report_date = Column(Date, nullable=False)

    holdings = relationship(
        "FundHolding",
        back_populates="fund",
        cascade="all, delete-orphan"
    )

class FundHolding(Base):
    __tablename__ = "fund_holdings"

    id               = Column(Integer, primary_key=True, index=True)
    fund_id          = Column(
        Integer,
        ForeignKey("funds.id", ondelete="CASCADE"),
        nullable=False
    )
    security_id      = Column(
        Integer,
        ForeignKey("securities.id", ondelete="CASCADE"),
        nullable=False
    )
    pct_of_portfolio = Column(Numeric(7, 4), nullable=True)

    fund     = relationship("Fund", back_populates="holdings")
    security = relationship("Security", back_populates="fund_holdings")