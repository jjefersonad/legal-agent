"""
API Router - Aggregates all route modules.
"""

from fastapi import APIRouter

from api.routes.documents import router as documents_router
from api.routes.search import router as search_router
from api.routes.collections import router as collections_router

# Main API Router
api_router = APIRouter()

# Include all route modules
api_router.include_router(documents_router)
api_router.include_router(search_router)
api_router.include_router(collections_router)


__all__ = ["api_router"]
