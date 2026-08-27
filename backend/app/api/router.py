"""Top-level API router. Feature routers are included here."""

from fastapi import APIRouter

from app.api.routes import auth, health, projects, tags, tasks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
api_router.include_router(tags.router)
