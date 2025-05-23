from contextlib import asynccontextmanager
import uvicorn

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, AsyncGenerator

from .db import AsyncSessionLocal, engine, Base
from .models import Security, Document
from .schemas import SecuritySchema, DocumentSchema, DocumentCreate
from .utils.logging_helper import logger


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
        select(Security).options(selectinload(Security.documents))
    )
    return result.scalars().all()


# ----- Get single security by ISIN (with documents) -----
@app.get("/securities/{isin}", response_model=SecuritySchema)
async def get_security_by_isin(
    isin: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Security)
        .where(Security.isin == isin)
        .options(selectinload(Security.documents))
    )
    sec = result.scalar_one_or_none()
    if not sec:
        raise HTTPException(status_code=404, detail=f"Security with ISIN={isin} not found")
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
        raise HTTPException(status_code=404, detail=f"Security with ISIN={isin} not found")

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
