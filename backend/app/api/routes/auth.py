from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import OptionalUserDep, SessionDep, parse_anon_id
from app.core.config import get_settings
from app.core.security import create_session_token, hash_password, verify_password
from app.models import Rating, Run, StepVote, User
from app.schemas import LoginIn, MeOut, RegisterIn, UserMe

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session(response: Response, user: User) -> None:
    s = get_settings()
    response.set_cookie(
        s.session_cookie,
        create_session_token(user.id),
        max_age=s.session_days * 86400,
        httponly=True,
        samesite="lax",
        secure=s.cookie_secure,
        path="/",
    )


async def merge_guest(session: AsyncSession, user: User, raw_anon: str | None) -> None:
    anon = parse_anon_id(raw_anon)
    if not anon:
        return
    guest, me = f"a:{anon}", f"u:{user.id}"
    await session.execute(
        update(Run).where(Run.anon_id == anon, Run.user_id.is_(None)).values(user_id=user.id)
    )
    # гость и акк голосовали за один шаг - оставляем голос акка
    mine = select(StepVote.step_key, StepVote.version_id).where(StepVote.voter == me)
    await session.execute(
        delete(StepVote).where(
            StepVote.voter == guest,
            func.row(StepVote.step_key, StepVote.version_id).in_(mine),
        )
    )
    await session.execute(update(StepVote).where(StepVote.voter == guest).values(voter=me))
    rated = select(Rating.guide_id).where(Rating.voter == me)
    await session.execute(delete(Rating).where(Rating.voter == guest, Rating.guide_id.in_(rated)))
    await session.execute(
        update(Rating).where(Rating.voter == guest).values(voter=me, user_id=user.id)
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, response: Response, session: SessionDep) -> UserMe:
    email = body.email.lower()
    if await session.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Такой email уже зарегистрирован")
    user = User(email=email, name=body.name, password_hash=hash_password(body.password))
    session.add(user)
    await session.flush()
    await merge_guest(session, user, body.anon_id)
    await session.commit()
    _set_session(response, user)
    return UserMe.model_validate(user)


@router.post("/login")
async def login(body: LoginIn, response: Response, session: SessionDep) -> UserMe:
    user = await session.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный email или пароль")
    await merge_guest(session, user, body.anon_id)
    await session.commit()
    _set_session(response, user)
    return UserMe.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(get_settings().session_cookie, path="/")


@router.get("/me")
async def me(user: OptionalUserDep) -> MeOut:
    return MeOut(user=UserMe.model_validate(user) if user else None)
