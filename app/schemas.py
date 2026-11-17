"""Pydantic request/response models -- the API contract."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["todo", "doing", "done"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    detail: str = Field(default="", max_length=2000)
    status: Status = "todo"


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    detail: str | None = Field(default=None, max_length=2000)
    status: Status | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    detail: str
    status: Status
    created_at: datetime
    updated_at: datetime


class Stats(BaseModel):
    total: int
    todo: int
    doing: int
    done: int


class Health(BaseModel):
    status: str
    version: str
    environment: str
