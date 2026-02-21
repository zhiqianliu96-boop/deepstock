from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.base import init_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="DeepStock",
    description="Deep Stock Analysis — Data First, AI Second",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    import os
    from app.config import settings
    return {
        "status": "ok",
        "gemini_key_set": bool(settings.gemini_api_key),
        "tavily_key_set": bool(settings.tavily_api_key),
        "gemini_env": bool(os.environ.get("GEMINI_API_KEY")),
        "tavily_env": bool(os.environ.get("TAVILY_API_KEY")),
    }


if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
