from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import AdminDep, SessionDep
from app.core.catalog import CATEGORY_SLUGS
from app.db import utcnow
from app.models import AiCall, Guide, Run, StepEvent, User
from app.schemas import AdminStats, AdminUser, AdminUserPatch

router = APIRouter(prefix="/admin", tags=["admin"])


async def _admin_user(session: SessionDep, u: User) -> AdminUser:
    count = await session.scalar(select(func.count()).where(Guide.author_id == u.id))
    return AdminUser.model_validate(
        {
            **{k: getattr(u, k) for k in AdminUser.model_fields if hasattr(u, k)},
            "guides_count": count or 0,
        }
    )


@router.get("/stats")
async def admin_stats(session: SessionDep, _: AdminDep) -> AdminStats:
    day = utcnow() - timedelta(days=1)
    calls, cost_day = (
        await session.execute(
            select(func.count(), func.coalesce(func.sum(AiCall.cost_usd), 0.0)).where(
                AiCall.created_at > day
            )
        )
    ).one()
    return AdminStats(
        users=await session.scalar(select(func.count()).select_from(User)) or 0,
        guides=await session.scalar(select(func.count()).select_from(Guide)) or 0,
        runs=await session.scalar(select(func.count()).select_from(Run)) or 0,
        events=await session.scalar(select(func.count()).select_from(StepEvent)) or 0,
        ai_calls_24h=calls,
        ai_cost_24h=round(float(cost_day), 4),
        ai_cost_total=round(
            float(await session.scalar(select(func.coalesce(func.sum(AiCall.cost_usd), 0.0))) or 0),
            4,
        ),
        pending_expert_requests=await session.scalar(
            select(func.count()).where(User.expert_request_status == "pending")
        )
        or 0,
    )


@router.get("/users")
async def admin_users(
    session: SessionDep,
    _: AdminDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
    pending: bool = False,
) -> list[AdminUser]:
    stmt = select(User).order_by(User.created_at.desc()).limit(200)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(User.name).like(like), User.email.like(like)))
    if pending:
        stmt = stmt.where(User.expert_request_status == "pending")
    return [await _admin_user(session, u) for u in await session.scalars(stmt)]


@router.patch("/users/{user_id}")
async def admin_patch_user(
    user_id: int, body: AdminUserPatch, session: SessionDep, admin: AdminDep
) -> AdminUser:
    u = await session.get(User, user_id)
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    if u.id == admin.id and body.role != "admin":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя снять роль администратора с себя")
    u.role = body.role
    u.expert_categories = [c for c in body.expert_categories if c in CATEGORY_SLUGS]
    if body.role == "expert" and not u.expert_categories:
        u.expert_categories = list(u.expert_request_categories)
    if u.expert_request_status == "pending":
        u.expert_request_status = None if body.role == "expert" else "rejected"
    await session.commit()
    return await _admin_user(session, u)


@router.post("/users/{user_id}/reject-expert")
async def admin_reject_expert(user_id: int, session: SessionDep, _: AdminDep) -> AdminUser:
    u = await session.get(User, user_id)
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    u.expert_request_status = "rejected"
    await session.commit()
    return await _admin_user(session, u)
