# martini/main.py

import datetime
import os
import ipaddress
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, List

from dotenv import load_dotenv
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response, Query
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import MetaData, Table, Column, Integer, String, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as orm_select
from sqlalchemy.orm import selectinload

from google.cloud import storage
from google.oauth2 import service_account

from .db import AsyncSessionLocal, Base, engine
from .models import Document, Security, PriceHistory, AccessLog, Fund, FundHolding
from .schemas import DocumentCreate, DocumentSchema, SecuritySchema, SecurityListItemSchema
from .utils.logging_helper import logger

# ── Load environment variables ──
ROOT_DIR = Path(__file__).parents[1]
load_dotenv(dotenv_path=ROOT_DIR / ".env.local")

# ----- Initialize GCS client -----
credentials = service_account.Credentials.from_service_account_file(
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
)
gcs_client = storage.Client(credentials=credentials, project=credentials.project_id)
BUCKET_NAME = "dry-martini-docs"

# ----- Database initialization -----
async def init_models():
    logger.debug("Initializing database tables…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.debug("Database tables initialized.")

# ----- Lifespan handler ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the application.")
    await init_models()
    logger.info("Database initialized, ready to serve requests.")
    yield
    logger.info("Shutting down the application.")

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/", response_model=dict)
def root():
    return {"message": "Welcome to the Securities API"}

# ── Manually declare the security_popularity view ──
metadata = MetaData()
security_popularity = Table(
    "security_popularity",
    metadata,
    Column("id", Integer),
    Column("name", String),
    Column("isin", String),
    Column("fund_count", Integer),
    Column("access_count", Integer),
    Column("doc_count", Integer),
    Column("popularity", Integer),
)

@app.get("/securities", response_model=List[SecurityListItemSchema])
async def list_securities(
    skip: int = 0,
    limit: int = 100,
    sort: str = Query(
        "popularity",
        description="Sort field: popularity (default), isin, or name",
        regex="^(popularity|isin|name)$"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    List securities ordered by the given sort field, omitting null ISINs.
    """
    # Base projection & filter
    stmt = (
        select(
            security_popularity.c.id,
            security_popularity.c.name,
            security_popularity.c.isin,
        )
        .where(security_popularity.c.isin.is_not(None))
    )

    # Dynamic ordering
    if sort == "popularity":
        stmt = stmt.order_by(desc(security_popularity.c.popularity))
    elif sort == "isin":
        stmt = stmt.order_by(security_popularity.c.isin)
    else:  # name
        stmt = stmt.order_by(security_popularity.c.name)

    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        SecurityListItemSchema(id=row.id, name=row.name, isin=row.isin)
        for row in rows
    ]

@app.get("/securities/{isin}", response_model=SecuritySchema)
async def get_security_by_isin(
    isin: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 1) Fetch the security (with docs & history) and record access
    now_utc = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    sec_q = (
        select(Security)
        .where(Security.isin == isin)
        .options(
            selectinload(Security.documents),
            selectinload(Security.price_history)
        )
    )
    result = await db.execute(sec_q)
    sec = result.scalar_one_or_none()
    if not sec:
        raise HTTPException(status_code=404, detail=f"Security with ISIN={isin} not found")

    # record access
    try:
        ip_obj = ipaddress.ip_address(request.client.host)
    except ValueError:
        ip_obj = None
    access = AccessLog(
        security_id=sec.id,
        accessed_at=now_utc,
        client_ip=ip_obj,
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add(access)
    await db.commit()

    # proxy URLs
    base = str(request.base_url).rstrip("/")
    for doc in sec.documents:
        doc.url = f"{base}/documents/{doc.id}/proxy"

    # Fetch fund holdings
    holdings_q = (
        select(Fund.fund_name, FundHolding.pct_of_portfolio)
        .join(FundHolding, Fund.id == FundHolding.fund_id)
        .where(FundHolding.security_id == sec.id)
    )
    holdings_res = await db.execute(holdings_q)
    holdings = [
        {"fund_name": fn, "pct_of_portfolio": float(pct)}
        for fn, pct in holdings_res.all()
    ]

    # Return only the explicit fields
    return SecuritySchema(
        id=sec.id,
        name=sec.name,
        cusip=sec.cusip,
        isin=sec.isin,
        sedol=sec.sedol,
        documents=sec.documents,
        price_history=sec.price_history,
        fund_holdings=holdings,
    )

@app.post("/securities/{isin}/documents", response_model=DocumentSchema, status_code=201)
async def add_document_to_security(isin: str, payload: DocumentCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(orm_select(Security).where(Security.isin == isin))
    sec = result.scalar_one_or_none()
    if not sec:
        raise HTTPException(status_code=404, detail=f"Security with ISIN={isin} not found")
    doc = Document(security_id=sec.id, doc_type=payload.doc_type, url=payload.url)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc

@app.get("/documents/{doc_id}/proxy")
async def proxy_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(orm_select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    bucket = gcs_client.bucket(BUCKET_NAME)
    blob_name = doc.url.split(f"{BUCKET_NAME}/", 1)[-1]
    data = bucket.blob(blob_name).download_as_bytes()
    return Response(content=data, media_type="application/pdf")

if __name__ == "__main__":
    uvicorn.run("martini.main:app", host="::", port=6010, reload=True)
