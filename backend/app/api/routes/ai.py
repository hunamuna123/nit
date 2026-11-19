from fastapi import APIRouter

from app.api.deps import CurrentUserDep, OptionalUserDep, SessionDep
from app.core.config import get_settings
from app.schemas import (
    AiDraftIn,
    AiImportIn,
    AiImproveIn,
    AiImproveOut,
    AiReviewIn,
    AiReviewOut,
    AiStatus,
    GuideDraft,
)
from app.services import ai

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def ai_status(session: SessionDep, user: OptionalUserDep) -> AiStatus:
    s = get_settings()
    return AiStatus(
        enabled=s.ai_enabled,
        model=s.ai_model if not s.ai_fake else "fake",
        remaining_hour=await ai.remaining_for(session, user),
    )


@router.post("/draft")
async def ai_draft(body: AiDraftIn, session: SessionDep, user: CurrentUserDep) -> GuideDraft:
    return await ai.draft_from_topic(session, user, body.topic, body.details)


@router.post("/import")
async def ai_import(body: AiImportIn, session: SessionDep, user: CurrentUserDep) -> GuideDraft:
    return await ai.draft_from_text(session, user, body.text)


@router.post("/improve-step")
async def ai_improve(body: AiImproveIn, session: SessionDep, user: CurrentUserDep) -> AiImproveOut:
    return await ai.improve_step(
        session, user, body.guide_title, body.step.model_dump(), body.mode, body.instruction
    )


@router.post("/review")
async def ai_review(body: AiReviewIn, session: SessionDep, user: CurrentUserDep) -> AiReviewOut:
    return await ai.review_guide(
        session, user, body.title, body.summary, [s.model_dump() for s in body.steps]
    )
