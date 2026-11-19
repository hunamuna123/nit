from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db import Base, utcnow

EMBEDDING_DIM = get_settings().embedding_dim


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))
    # learner | expert | admin
    role: Mapped[str] = mapped_column(String(16), default="learner")
    bio: Mapped[str] = mapped_column(Text, default="")
    expert_categories: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list)
    expert_request_status: Mapped[str | None] = mapped_column(String(16))
    expert_request_text: Mapped[str | None] = mapped_column(Text)
    expert_request_categories: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list)
    expert_requested_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True, default="study")
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    difficulty: Mapped[int] = mapped_column(SmallInteger, default=1)
    cover: Mapped[str] = mapped_column(String(16), default="torus")
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)

    title: Mapped[str] = mapped_column(String(160), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    est_minutes: Mapped[int] = mapped_column(Integer, default=0)
    steps_count: Mapped[int] = mapped_column(Integer, default=0)

    draft_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_versions.id", use_alter=True, ondelete="SET NULL")
    )
    published_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_versions.id", use_alter=True, ondelete="SET NULL")
    )
    forked_from_id: Mapped[int | None] = mapped_column(
        ForeignKey("guides.id", ondelete="SET NULL"), index=True
    )

    verified_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    verified_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_versions.id", use_alter=True, ondelete="SET NULL")
    )
    verified_at: Mapped[datetime | None]

    runs_count: Mapped[int] = mapped_column(Integer, default=0)
    completions_count: Mapped[int] = mapped_column(Integer, default=0)
    rating_sum: Mapped[int] = mapped_column(Integer, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    helpful_up: Mapped[int] = mapped_column(Integer, default=0)
    helpful_down: Mapped[int] = mapped_column(Integer, default=0)
    forks_count: Mapped[int] = mapped_column(Integer, default=0)

    search_text: Mapped[str] = mapped_column(Text, default="")
    search_tsv: Mapped[Any] = mapped_column(TSVECTOR, nullable=True)
    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow)
    published_at: Mapped[datetime | None]

    author: Mapped[User] = relationship(foreign_keys=[author_id], lazy="raise")
    verified_by: Mapped[User | None] = relationship(foreign_keys=[verified_by_id], lazy="raise")
    forked_from: Mapped["Guide | None"] = relationship(remote_side=[id], lazy="raise")

    __table_args__ = (
        Index("ix_guides_search_tsv", "search_tsv", postgresql_using="gin"),
        Index(
            "ix_guides_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )


class GuideVersion(Base):
    __tablename__ = "guide_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    # 0 черновик, дальше опубликованные
    number: Mapped[int] = mapped_column(Integer, default=0)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True)
    title: Mapped[str] = mapped_column(String(160), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    changelog: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
    published_at: Mapped[datetime | None]

    steps: Mapped[list["Step"]] = relationship(
        order_by="Step.position", cascade="all, delete-orphan", lazy="raise"
    )


class Step(Base):
    __tablename__ = "steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("guide_versions.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(36))
    position: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    minutes: Mapped[int] = mapped_column(Integer, default=5)
    checklist: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("guide_versions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    anon_id: Mapped[str | None] = mapped_column(String(36), index=True)
    # active | completed
    status: Mapped[str] = mapped_column(String(16), default="active")
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    # {"checked": {step_key: [item_key]}, "done": [step_key]}
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(default=utcnow)
    completed_at: Mapped[datetime | None]


class StepEvent(Base):
    __tablename__ = "step_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[int] = mapped_column(Integer, index=True)
    step_key: Mapped[str] = mapped_column(String(36))
    # view | complete | stuck | reopen
    type: Mapped[str] = mapped_column(String(16))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    client_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class StepVote(Base):
    __tablename__ = "step_votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[int] = mapped_column(Integer)
    step_key: Mapped[str] = mapped_column(String(36))
    # "u:<id>" или "a:<anon uuid>"
    voter: Mapped[str] = mapped_column(String(48))
    value: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    __table_args__ = (UniqueConstraint("version_id", "step_key", "voter", name="uq_step_vote"),)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[int | None] = mapped_column(Integer)
    step_key: Mapped[str | None] = mapped_column(String(36), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16), default="comment")
    body: Mapped[str] = mapped_column(Text)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    user: Mapped[User] = relationship(lazy="raise")


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    voter: Mapped[str] = mapped_column(String(48))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    value: Mapped[int] = mapped_column(SmallInteger)
    review: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    __table_args__ = (UniqueConstraint("guide_id", "voter", name="uq_rating_voter"),)


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    base_version_id: Mapped[int] = mapped_column(Integer)
    step_key: Mapped[str] = mapped_column(String(36))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    reply: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    resolved_at: Mapped[datetime | None]

    user: Mapped[User] = relationship(lazy="raise")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[int] = mapped_column(Integer)
    expert_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    verdict: Mapped[str] = mapped_column(String(16))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    expert: Mapped[User] = relationship(lazy="raise")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    __table_args__ = (UniqueConstraint("user_id", "guide_id", name="uq_bookmark"),)


class AiCall(Base):
    __tablename__ = "ai_calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(80))
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(default=0.0)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
