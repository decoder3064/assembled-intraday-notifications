import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RuleRow(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_type: Mapped[str]
    scope: Mapped[dict] = mapped_column(JSONB)
    params: Mapped[dict] = mapped_column(JSONB)
    recipient_id: Mapped[str]
    description: Mapped[str]
    severity: Mapped[int]
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class RuleStateRow(Base):
    """Not used yet, but in production this would be worth wiring up: it
    would store which rules are currently firing, so that state survives
    a server restart instead of living only in memory. Without it, a
    restart can cause one repeat notification for whatever was already
    firing at the time."""

    __tablename__ = "rule_state"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rules.id", ondelete="CASCADE"))
    entity_key: Mapped[str]
    status: Mapped[str] = mapped_column(default="ok")  # "ok" | "firing"
    fired_at: Mapped[datetime | None]
    last_notified_at: Mapped[datetime | None]


class NotificationRow(Base):
    """rule_id is nullable and set to NULL (not cascaded) when the owning
    rule is deleted — a notification's message, severity, and recipient are
    already stored on the row itself, so the notification stays meaningful
    on its own even once the rule that caused it is gone. History is kept
    on purpose; only the backlink to the (now-deleted) rule is lost."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rules.id", ondelete="SET NULL"), nullable=True)
    recipient_id: Mapped[str]
    message: Mapped[str]
    severity: Mapped[int]
    resolved: Mapped[bool] = mapped_column(default=False)
    sent_at: Mapped[datetime] = mapped_column(server_default=func.now())
