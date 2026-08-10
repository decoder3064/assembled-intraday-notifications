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


class NotificationRow(Base):
    """rule_id is set to NULL (not cascaded) when the rule is deleted, so
    notification history survives."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rules.id", ondelete="SET NULL"), nullable=True)
    rule_type: Mapped[str | None]
    recipient_id: Mapped[str]
    message: Mapped[str]
    severity: Mapped[int]
    resolved: Mapped[bool] = mapped_column(default=False)
    sent_at: Mapped[datetime] = mapped_column(server_default=func.now())
