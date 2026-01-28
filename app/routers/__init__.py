# app/routers/__init__.py
from .health import router as health_router
from .cases import router as cases_router
from .documents import router as documents_router

__all__ = ["health_router", "cases_router", "documents_router"]
