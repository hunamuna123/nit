import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import read_session_token
from app.db import get_session
from app.models import User

SessionDep = Annotated[AsyncSession, Depends(get_session)]

ANON_HEADER = "x-nit-anon"


async def get_optional_user(request: Request, session: SessionDep) -> User | None:
    token = request.cookies.get(get_settings().session_cookie)
    if not token:
        return None
    user_id = read_session_token(token)
    if user_id is None:
        return None
    return await session.get(User, user_id)


OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]


async def get_current_user(user: OptionalUserDep) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Нужно войти в аккаунт")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_expert(user: CurrentUserDep) -> User:
    if user.role not in ("expert", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Только для экспертов")
    return user


ExpertDep = Annotated[User, Depends(get_expert)]


async def get_admin(user: CurrentUserDep) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Только для администраторов")
    return user


AdminDep = Annotated[User, Depends(get_admin)]


def parse_anon_id(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        return str(uuid.UUID(raw))
    except ValueError:
        return None


@dataclass
class Viewer:
    user: User | None
    anon_id: str | None

    @property
    def key(self) -> str | None:
        if self.user:
            return f"u:{self.user.id}"
        if self.anon_id:
            return f"a:{self.anon_id}"
        return None

    def require_key(self) -> str:
        key = self.key
        if key is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нет идентификатора гостя")
        return key


async def get_viewer(request: Request, user: OptionalUserDep) -> Viewer:
    return Viewer(user=user, anon_id=parse_anon_id(request.headers.get(ANON_HEADER)))


ViewerDep = Annotated[Viewer, Depends(get_viewer)]
