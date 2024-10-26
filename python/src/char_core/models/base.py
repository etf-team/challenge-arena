from __future__ import annotations

from datetime import datetime
from typing import TypeAlias, Annotated

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    pass


CreatedAt: TypeAlias = Annotated[
    datetime,
    mapped_column(default=datetime.now),
]
IntegerPk: TypeAlias = Annotated[
    int,
    mapped_column(primary_key=True, autoincrement=True),
]
