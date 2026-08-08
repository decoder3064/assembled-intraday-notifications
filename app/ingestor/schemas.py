from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class QueueSnapshot(BaseModel):
    event_id: str
    ts: datetime
    type: Literal["queue_snapshot"]
    queue_id: str
    tickets_waiting: int
    longest_wait_sec: int
    sla_target_sec: int
    agents_available: int
    agents_on_call: int
    volume_last_15m: int
    volume_forecast_next_15m: int | None = None


class AgentStateChange(BaseModel):
    event_id: str
    ts: datetime
    type: Literal["agent_state_change"]
    agent_id: str
    queue_ids: list[str] = []
    previous_state: str | None = None
    previous_state_duration_sec: int | None = None
    new_state: str

    @field_validator("queue_ids", mode="before")
    @classmethod
    def normalize_queue_ids(cls, v):
        return v or []


class AdherenceCheck(BaseModel):
    event_id: str
    ts: datetime
    type: Literal["adherence_check"]
    agent_id: str
    queue_ids: list[str] = []
    scheduled_state: str
    actual_state: str
    in_violation: bool
    violation_started_at: datetime | None = None

    @field_validator("queue_ids", mode="before")
    @classmethod
    def normalize_queue_ids(cls, v):
        return v or []


Event = QueueSnapshot | AgentStateChange | AdherenceCheck
