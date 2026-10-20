"""Version 1 route registration."""

from fastapi import APIRouter, Depends

from app.api.deps import enforce_csrf
from app.api.v1.admin import router as admin_router
from app.api.v1.admin_catalog import router as admin_catalog_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as category_router
from app.api.v1.health import router as health_router
from app.api.v1.products import router as product_router

api_router = APIRouter(dependencies=[Depends(enforce_csrf)])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(category_router)
api_router.include_router(product_router)
api_router.include_router(admin_router)
api_router.include_router(admin_catalog_router)
