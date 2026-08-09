import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# This system is scoped to one team with one team lead (see decisions.md) —
# every rule notifies the same recipient, so there's nothing for a rule
# author to choose here. The column survives in the DB for schema stability;
# only the API contract drops it.
DEFAULT_RECIPIENT_ID = "lead_maria"


class RuleCreate(BaseModel):
    rule_type: str
    scope: dict
    params: dict
    severity: int = Field(ge=1, le=10)
    description: str


class RuleUpdate(BaseModel):
    scope: dict | None = None
    params: dict | None = None
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
    rule_type: str | None
    recipient_id: str
    message: str
    severity: int
    resolved: bool
    sent_at: datetime

    model_config = {"from_attributes": True}
