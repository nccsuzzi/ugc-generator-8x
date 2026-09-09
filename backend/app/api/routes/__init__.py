from app.api.routes.health import router as health_router
from app.api.routes.chat import router as chat_router
from app.api.routes.videos import router as videos_router
from app.api.routes.products import router as products_router

__all__ = ["health_router", "chat_router", "videos_router", "products_router"]
