from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.routes import health_router, chat_router, videos_router, products_router
from app.utils.file_utils import ensure_dir


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and temp/asset directories exist
    init_db()
    ensure_dir(settings.TEMP_DIR)
    ensure_dir(settings.ASSETS_DIR / "backgrounds")
    ensure_dir(settings.ASSETS_DIR / "gifs")
    ensure_dir(settings.ASSETS_DIR / "audio")
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes (support both /api/v1 and /v1 prefixes for Vercel Serverless compatibility)
for prefix in [settings.API_V1_STR, "/v1"]:
    app.include_router(health_router, prefix=prefix, tags=["Health"])
    app.include_router(chat_router, prefix=prefix, tags=["Chat"])
    app.include_router(videos_router, prefix=prefix, tags=["Videos"])
    app.include_router(products_router, prefix=prefix, tags=["Products"])


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs",
        "api": settings.API_V1_STR,
    }
