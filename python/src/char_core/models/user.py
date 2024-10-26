from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, TypeAlias

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


CreatedAt: TypeAlias = Annotated[
    datetime,
    mapped_column(default=datetime.now),
]
IntegerPk: TypeAlias = Annotated[
    int,
    mapped_column(primary_key=True, autoincrement=True),
]


class User(Base):
    __tablename__ = "user"

    id: Mapped[IntegerPk]
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    full_name: Mapped[str]
    description: Mapped[str | None]
    created_at: Mapped[CreatedAt]


class SpaceMemberRoleEnum(Enum):
    ADMINISTRATOR = "ADMINISTRATOR"
    PARTICIPANT = "PARTICIPANT"


class SpaceMember(Base):
    __tablename__ = "space_member"

    id: Mapped[IntegerPk]
    role: Mapped[SpaceMemberRoleEnum]
    space_id: Mapped[int] = mapped_column(ForeignKey("space.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[CreatedAt]


class Space(Base):
    __tablename__ = "space"

    id: Mapped[IntegerPk]
    name: Mapped[str]
    invitation_token: Mapped[str]
    created_at: Mapped[CreatedAt]


class Achievement(Base):
    __tablename__ = "achievement"

    id: Mapped[IntegerPk]
    name: Mapped[str]
    created_at: Mapped[CreatedAt]


class AchievementAssignation(Base):
    __tablename__ = "achievement_assignation"

    id: Mapped[IntegerPk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    created_at: Mapped[CreatedAt]


class Challenge(Base):
    __tablename__ = "challenge"

    id: Mapped[IntegerPk]
    name: Mapped[str]
    prize: Mapped[str]
    created_at: Mapped[CreatedAt]
