from fastapi import FastAPI
from pathlib import Path
from contextlib import asynccontextmanager
from app.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    init_db()
    Path("data/files").mkdir(parents=True, exist_ok=True)
    yield
    # shutdown (sau này cần thì thêm)

app = FastAPI(
    title="Notary ERP",
    lifespan=lifespan,
)

@app.get("/health")
def health():
    return {"ok": True}
