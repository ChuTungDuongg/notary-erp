from fastapi import FastAPI
from pathlib import Path
from contextlib import asynccontextmanager

from app.db import init_db

from app.routers.health import router as health_router
from app.routers.cases import router as cases_router
from app.routers.documents import router as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    Path("data/files").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Notary ERP",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(cases_router)
app.include_router(documents_router)
