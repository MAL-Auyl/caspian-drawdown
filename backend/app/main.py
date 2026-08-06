from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.api.v1 import router as v1_router
from app.services import reports_db
from app.services.store import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.load()
    reports_db.init_db()
    yield


app = FastAPI(title="Caspian Pulse API", version="0.1.0", lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(v1_router, prefix="/api/v1")
