from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from char_core.models.base import Base, CreatedAt, IntegerPk

if TYPE_CHECKING:
    from char_core.models.challenge import AchievementAssignation


class User(Base):
    __tablename__ = "user"

    id: Mapped[IntegerPk]
    email: Mapped[str] = mapped_column(unique=True)
    phone_number: Mapped[int | None] = mapped_column(BigInteger)
    password_hash: Mapped[str]
    full_name: Mapped[str]
    description: Mapped[str | None]
    created_at: Mapped[CreatedAt]
    achievements_assignations: Mapped[list[AchievementAssignation]] = relationship(
        primaryjoin="AchievementAssignation.user_id == User.id",
        lazy="selectin",
        viewonly=True,
    )

    def __str__(self):
        return f"{self.full_name} <{self.email}>"
