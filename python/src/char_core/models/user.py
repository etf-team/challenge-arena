from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, TypeAlias
from uuid import uuid4
from sqlalchemy import (
    ForeignKey,
    CheckConstraint,
    case,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession


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


class User(Base):
    __tablename__ = "user"

    id: Mapped[IntegerPk]
    email: Mapped[str] = mapped_column(unique=True)
    phone_number: Mapped[int | None] = mapped_column()
    password_hash: Mapped[str]
    full_name: Mapped[str]
    description: Mapped[str | None]
    created_at: Mapped[CreatedAt]
    achievements_assignations: Mapped[list[AchievementAssignation]] = relationship(
        primaryjoin="AchievementAssignation.user_id == User.id",
        lazy="selectin",
        viewonly=True,
    )


class SpaceMember(Base):
    __tablename__ = "space_member"

    id: Mapped[IntegerPk]
    is_administrator: Mapped[bool] = mapped_column(default=False)
    space_id: Mapped[int] = mapped_column(ForeignKey("space.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[CreatedAt]


class Space(Base):
    __tablename__ = "space"

    id: Mapped[IntegerPk]
    name: Mapped[str]
    description: Mapped[str | None]
    invitation_token: Mapped[str] = mapped_column(
        default=lambda: str(uuid4()),
    )
    created_at: Mapped[CreatedAt]
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
    ) -> SpaceMember:
        stmt = (
            select(SpaceMember)
            .where(SpaceMember.user_id == user.id)
        )
        member = await session.scalar(stmt)
        if member is None:
            raise AccessDenied()
        if edit and not member.is_administrator:
            raise AccessDenied()

        return member

    def __str__(self):
        return self.name


class Achievement(Base):
    __tablename__ = "achievement"

    id: Mapped[IntegerPk]
    name: Mapped[str]
    space_id: Mapped[int] = mapped_column(ForeignKey("space.id"))
    created_at: Mapped[CreatedAt]

    space: Mapped[Space] = relationship(back_populates="achievements")

    def __str__(self):
        return self.name


class AchievementAssignation(Base):
    __tablename__ = "achievement_assignation"

    id: Mapped[IntegerPk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievement.id"))
    created_at: Mapped[CreatedAt]

    challenge: Mapped[Challenge] = relationship()
    user: Mapped[User] = relationship()
    achievement: Mapped[Achievement] = relationship(lazy="selectin")


class AccessDenied(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=403,
            detail="Access denied",
        )


class ChallengeMemberRoleEnum(Enum):
    ANY = "ANY"
    REFREE = "REFREE"
    PARTICIPANT = "PARTICIPANT"
    ADMINISTRATOR = "ADMINISTRATOR"


class AggregationStrategy(Enum):
    SUM = "SUM"
    AVG = "AVG"
    MAX = "MAX"


class SelectionFnEnum(Enum):
    HIGHER_THAN = "HIGHER_THAN"
    LESS_THAN = "LESS_THAN"
    HEAD = "HEAD"
    TAIL = "TAIL"


class SelectionStrategy(Enum):
    fn: SelectionFnEnum
    argument: Mapped[float]


class ChallengeResult(Base):
    __tablename__ = "challenge_result"

    id: Mapped[IntegerPk]
    member_id: Mapped[int] = mapped_column(ForeignKey("challenge_member.id"))
    submitted_value: Mapped[float]  # assigned by submitter
    estimation_value: Mapped[float | None]  # may be assigned by refree
    verification_value: Mapped[float | None]  # may be assigned by administrator
    created_at: Mapped[CreatedAt]

    member: Mapped[ChallengeMember] = relationship()

    def __str__(self):
        result = f"{self.submitted_value}"
        if self.estimation_value is not None:
            result += f" estimation={self.estimation_value}"
        if self.verification_value is not None:
            result += f" verification={self.verification_value}"

        return result


class ChallengeMember(Base):
    __tablename__ = "challenge_member"

    id: Mapped[IntegerPk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))
    is_referee: Mapped[bool] = mapped_column(default=False)
    is_participant: Mapped[bool] = mapped_column(default=False)
    is_administrator: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[CreatedAt]

    user: Mapped[User] = relationship(lazy="selectin")
    challenge: Mapped[Challenge] = relationship(
        back_populates="members",
    )

    def __str__(self):
        parts = []
        if self.is_administrator:
            parts.append("admin")
        if self.is_referee:
            parts.append("refree")
        if self.is_participant:
            parts.append("participant")

        result = f"{self.user.full_name}"
        if parts:
            result += f" [{', '.join(parts)}]"
        return result


class ChallengeStateEnum(Enum):
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"


class Challenge(Base):
    __tablename__ = "challenge"

    id: Mapped[IntegerPk]
    space_id: Mapped[int] = mapped_column(ForeignKey("space.id"))
    name: Mapped[str]
    description: Mapped[str]
    prize: Mapped[str | None]
    achievement_id: Mapped[int | None] = mapped_column(
        ForeignKey("achievement.id"),
    )
    is_verification_required: Mapped[bool]
    is_estimation_required: Mapped[bool]

    starts_at: Mapped[datetime]
    ends_at_const: Mapped[datetime | None]
    ends_at_determination_fn: Mapped[SelectionFnEnum]
    ends_at_determination_argument: Mapped[float]

    cached_current_progress: Mapped[int] = mapped_column(default=0)

    results_aggregation_strategy: Mapped[AggregationStrategy]

    prize_determination_fn: Mapped[SelectionFnEnum]
    prize_determination_argument: Mapped[float]

    created_at: Mapped[CreatedAt]

    space: Mapped[Space] = relationship(lazy="selectin")
    members: Mapped[list[ChallengeMember]] = relationship(
        back_populates="challenge",
        lazy="selectin",
    )
    results: Mapped[list[ChallengeResult]] = relationship(
        lazy="selectin",
        secondary=ChallengeMember.__table__,
        viewonly=True,
    )
    achievement: Mapped[Achievement] = relationship()

    __table_args__ = (
        CheckConstraint("cached_current_progress >= 0 "
                        "and cached_current_progress <= 100"),
    )

    @hybrid_property
    def state(self) -> str:
        current_datetime = datetime.now()

        if self.starts_at > current_datetime:
            return ChallengeStateEnum.SCHEDULED.value
        elif self.cached_current_progress >= 100:
            return ChallengeStateEnum.FINISHED.value
        else:
            return ChallengeStateEnum.ACTIVE.value

    @state.inplace.expression
    @classmethod
    def _state_expr(cls):
        return case(
            (cls.starts_at > func.now(), ChallengeStateEnum.SCHEDULED.value),
            (cls.cached_current_progress >= 100, ChallengeStateEnum.ACTIVE.value),
            else_=ChallengeStateEnum.ACTIVE.value,
        )

    @property
    def active_results(self):
        def is_valid(result: ChallengeResult):
            conditions = [
                (not self.is_estimation_required
                 or result.estimation_value is not None),
                (not self.is_verification_required
                 or result.verification_value is not None),
            ]
            return all(conditions)

        return list(filter(is_valid, self.results))

    async def ensure_access(
            self,
            user: User,
            just_view: bool = False,
            administrator: bool = False,
            participant: bool = False,
            refree: bool = False,
    ):
        if just_view:
            space_members = await self.space.awaitable_attrs.members
            members = [i for i in space_members if i.user_id == user.id]
            if not members:
                raise AccessDenied()
            else:
                return None

        members = await self.awaitable_attrs.members
        members = [i for i in members if i.user_id == user.id]
        if len(members) == 0:
            raise AccessDenied()
        member: ChallengeMember = members[0]

        is_valid = True

        if administrator and not member.is_administrator:
            is_valid = False
        if participant and not member.is_participant:
            is_valid = False
        if refree and not member.is_referee:
            is_valid = False

        if not is_valid:
            raise AccessDenied()

        return member

    def __str__(self):
        return self.name
