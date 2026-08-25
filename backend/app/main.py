from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app import models
from app.routers import auth, messages, posts, users

Base.metadata.create_all(bind=engine)


app = FastAPI(title="DailyConnect API", version="1.0.0")
upload_directory = Path(__file__).resolve().parents[1] / "uploads"
upload_directory.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_directory), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "DailyConnect API"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(messages.router)
