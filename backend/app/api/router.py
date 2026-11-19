from fastapi import APIRouter

from app.api.routes import (
    admin,
    ai,
    auth,
    guides,
    health,
    meta,
    review,
    runs,
    studio,
    uploads,
    users,
)

api_router = APIRouter()
for module in (health, auth, meta, guides, runs, studio, ai, users, review, admin, uploads):
    api_router.include_router(module.router)
