"""Schémas de rétention : statut, propriétaire et journal des actions."""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

RetentionStatus = Literal[
    "none", "to_contact", "contacted", "retained", "ignored"
]
ActionType = Literal["call", "email", "discount", "onboarding", "other"]
ActionStatus = Literal["todo", "in_progress", "done", "cancelled"]


class CustomerRetentionUpdate(BaseModel):
    retention_status: Optional[RetentionStatus] = None
    owner_user_id: Optional[int] = None


class CustomerRetentionRead(BaseModel):
    customer_id: int
    external_id: str
    name: Optional[str] = None
    retention_status: RetentionStatus
    owner_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SuggestedAction(BaseModel):
    action_type: ActionType
    label: str
    feature: Optional[str] = None
    impact: float = 0.0


class CustomerActionCreate(BaseModel):
    action_type: ActionType
    status: ActionStatus = "todo"
    note: Optional[str] = Field(None, max_length=4000)
    due_date: Optional[date] = None


class CustomerActionUpdate(BaseModel):
    action_type: Optional[ActionType] = None
    status: Optional[ActionStatus] = None
    note: Optional[str] = Field(None, max_length=4000)
    due_date: Optional[date] = None


class CustomerActionRead(BaseModel):
    id: int
    customer_id: int
    created_by_user_id: Optional[int] = None
    action_type: ActionType
    status: ActionStatus
    note: Optional[str] = None
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
