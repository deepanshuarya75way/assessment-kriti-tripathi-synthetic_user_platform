from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic pagination envelope (spec §28)."""

    items: list[T]
    total: int
    page: int
    page_size: int


class Message(BaseModel):
    detail: str
