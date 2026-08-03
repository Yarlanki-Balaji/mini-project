import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Strategy(Base):
    __tablename__ = "strategies"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    idea_text: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CategoryInsight(Base):
    __tablename__ = "category_insights"
    __table_args__ = (UniqueConstraint("category", "agent"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    category: Mapped[str] = mapped_column(String)
    agent: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)
    dataset: Mapped[str] = mapped_column(String)
    sample_size: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class GuestSession(Base):
    __tablename__ = "guest_sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    fingerprint: Mapped[str] = mapped_column(String, unique=True)
    tries_used: Mapped[int] = mapped_column(Integer, default=0)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ShareToken(Base):
    __tablename__ = "share_tokens"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"))
    token: Mapped[str] = mapped_column(String, unique=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
