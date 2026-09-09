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

# Mount API routes
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(chat_router, prefix=settings.API_V1_STR, tags=["Chat"])
app.include_router(videos_router, prefix=settings.API_V1_STR, tags=["Videos"])
app.include_router(products_router, prefix=settings.API_V1_STR, tags=["Products"])


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs",
        "api": settings.API_V1_STR,
    }
