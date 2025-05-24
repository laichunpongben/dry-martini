# main.py

import datetime
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, List

from dotenv import load_dotenv
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage
from google.oauth2 import service_account
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .db import AsyncSessionLocal, Base, engine
from .models import Document, Security, PriceHistory
from .schemas import DocumentCreate, DocumentSchema, SecuritySchema
from .utils.logging_helper import logger

# ── Load environment variables from .env.local at project root ──
ROOT_DIR = Path(__file__).parents[1]
load_dotenv(dotenv_path=ROOT_DIR / ".env.local")
# ───────────────────────────────────────────────────────────────

# ----- Initialize GCS client once at startup -----
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

# ----- Lifespan handler -----
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the application.")
    await init_models()
    logger.info("Database initialized, ready to serve requests.")
    yield
    logger.info("Shutting down the application.")

# Create FastAPI app with our lifespan
app = FastAPI(lifespan=lifespan)

# ----- CORS Middleware -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Dependency: get async DB session -----
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# ----- Root endpoint -----
@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Welcome to the Securities API"}

# ----- List all securities (with documents) -----
@app.get("/securities", response_model=List[SecuritySchema])
async def list_securities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Security)
        .options(
            selectinload(Security.documents),
            selectinload(Security.price_history),
        )
    )
    return result.scalars().all()

# ----- Get single security by ISIN (with signed document URLs + price history) -----
@app.get("/securities/{isin}", response_model=SecuritySchema)
async def get_security_by_isin(
    isin: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Security)
        .where(Security.isin == isin)
        .options(
            selectinload(Security.documents),
            selectinload(Security.price_history),
        )
    )
    sec = result.scalar_one_or_none()
    if not sec:
        raise HTTPException(
            status_code=404,
            detail=f"Security with ISIN={isin} not found"
        )

    # generate signed URLs for documents
    bucket = gcs_client.bucket(BUCKET_NAME)
    for doc in sec.documents:
        blob_name = doc.url.split(f"{BUCKET_NAME}/", 1)[-1]
        blob = bucket.blob(blob_name)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="GET",
        )
        doc.url = signed_url

    return sec

# ----- Attach a new document to a security -----
@app.post(
    "/securities/{isin}/documents",
    response_model=DocumentSchema,
    status_code=201
)
async def add_document_to_security(
    isin: str,
    payload: DocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Security).where(Security.isin == isin))
    sec = result.scalar_one_or_none()
    if not sec:
        raise HTTPException(
            status_code=404,
            detail=f"Security with ISIN={isin} not found"
        )

    doc = Document(
        security_id=sec.id,
        doc_type=payload.doc_type,
        url=payload.url
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return doc

# ----- Uvicorn entry point -----
if __name__ == "__main__":
    uvicorn.run(
        "martini.main:app",
        host="::",
        port=6010,
        reload=True,
    )
