from __future__ import annotations

from uuid import uuid4

from sqlalchemy import ForeignKey, select, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from char_core.models.base import Base, IntegerPk, CreatedAt
from char_core.models.user import User
from char_core.models.challenge import Achievement
from char_core.exceptions import AccessDenied


class SpaceMember(Base):
    __tablename__ = "space_member"

    id: Mapped[IntegerPk]
    is_administrator: Mapped[bool] = mapped_column(default=False)
    space_id: Mapped[int] = mapped_column(ForeignKey("space.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[CreatedAt]

    space: Mapped[Space] = relationship(
        back_populates="members",
    )
    user: Mapped[User] = relationship(
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "space_id",
        ),
    )


class Space(Base):
    __tablename__ = "space"

    id: Mapped[IntegerPk]
    name: Mapped[str]
    description: Mapped[str | None]
    invitation_token: Mapped[str] = mapped_column(
        default=lambda: str(uuid4()),
    )
    created_at: Mapped[CreatedAt]
    members_count: Mapped[int] = mapped_column(default=0)
    members: Mapped[list[SpaceMember]] = relationship()
    achievements: Mapped[list[Achievement]] = relationship(
        lazy="selectin",
        back_populates="space",
    )

    async def ensure_access(
            self,
            session: AsyncSession,
            user: User,
            edit: bool = False,
            create_challenge: bool = False,
    ) -> SpaceMember:
        stmt = (
            select(SpaceMember)
            .where(SpaceMember.user_id == user.id)
            .where(SpaceMember.space_id == self.id)
        )
        member = await session.scalar(stmt)
        if member is None:
            raise AccessDenied()
        if (edit or create_challenge) and not member.is_administrator:
            raise AccessDenied()

        return member

    def __str__(self):
        return self.name
