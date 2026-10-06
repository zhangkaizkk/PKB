"""通用响应类型。"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class ApiError(BaseModel):
    detail: str


class DatetimeMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
