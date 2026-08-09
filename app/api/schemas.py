import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RuleCreate(BaseModel):
    rule_type: str
    scope: dict
    params: dict
    recipient_id: str
    severity: int = Field(ge=1, le=10)
    description: str


class RuleUpdate(BaseModel):
    scope: dict | None = None
    params: dict | None = None
    recipient_id: str | None = None
    severity: int | None = Field(default=None, ge=1, le=10)
    description: str | None = None
    enabled: bool | None = None


class RuleOut(BaseModel):
    id: uuid.UUID
    rule_type: str
    scope: dict
    params: dict
    recipient_id: str
    severity: int
    description: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationUpdate(BaseModel):
    resolved: bool | None = None


class NotificationOut(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID | None
    recipient_id: str
    message: str
    severity: int
    resolved: bool
    sent_at: datetime

    model_config = {"from_attributes": True}
