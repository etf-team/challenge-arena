from __future__ import annotations

from datetime import datetime
from enum import Enum
from select import select
from typing import Annotated, TypeAlias

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.ext.asyncio import AsyncSession


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


class AccessDenied(BaseException):
    pass


class ChallengeMemberRoleEnum(Base):
    ANY = "ANY"
    ADMINISTRATOR = "ADMINISTRATOR"
    PARTICIPANT = "PARTICIPANT"


class ChallengeMember(Base):
    __tablename__ = "challenge_member"

    role: Mapped[ChallengeMemberRoleEnum]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.id"))

    __mapper_args__ = {
        "polymorphic_identity": "challenge_member",
        "plymorphic_on": "role",
    }
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role",
        ),
    )


class ChallengeAccessKey(Base):
    EDIT = "EDIT"
    VOTE = "VOTE"
    JOIN = "JOIN"


class ChallengeACL(Base):
    __tablename__ = "challenge_acl"

    key: Mapped[ChallengeAccessKey]
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))


class ChallengeParticipantReport(Base):
    __tablename__ = "challenge_participant_report"

    created_at: Mapped[CreatedAt]
    amount: Mapped[int]


class ChallengeParticipant(ChallengeMember):
    __tablename__ = "challenge_member"

    id: Mapped[IntegerPk] = mapped_column(ForeignKey("challenge_member.id"))

    absolute_amount: Mapped[int] = mapped_column()
    photo_url: Mapped[str] = mapped_column()
    is_submitted: Mapped[bool] = mapped_column(default=False)

    __mapper_args__ = {
        "polymorphic_identity": ChallengeMemberRoleEnum.PARTICIPANT,
    }


class ChallengeAdministrator(ChallengeMember):
    __tablename__ = "challenge_administartor"

    id: Mapped[IntegerPk] = mapped_column(ForeignKey("challenge_member.id"))

    __mapper_args__ = {
        "polymorphic_identity": ChallengeMemberRoleEnum.ADMINISTRATOR,
    }

class ChallengeTargetAggregationFunction(Base):
    pass


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


class ChallengeTypeEnum(Enum):
    QUALITIVE = "QUALITIVE"
    QUANTITATIVE = "QUANTITATIVE"


class ChallengeReport(Base):
    __tablename__ = "challenge_report"

    id: Mapped[IntegerPk]
    estimation: Mapped[int] = mapped_column()
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("challenge_participant.id"),
    )
    created_at: Mapped[CreatedAt]


class ChallengeParticipant(Base):
    __tablename__ = "challenge_participant"

    id: Mapped[IntegerPk]
    user_id: Mapped[int] = mapped_column("user.id")
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenge.ud"))
    is_owner: Mapped[bool] = mapped_column(default=False)
    is_referee: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[CreatedAt]


class Challenge(Base):
    __tablename__ = "challenge"

    id: Mapped[IntegerPk]
    name: Mapped[str]
    type: ChallengeTypeEnum
    prize: Mapped[str]

    starts_at: Mapped[datetime]
    ends_at_const: Mapped[datetime | None]
    ends_at_determination_fn: Mapped[SelectionFnEnum]
    ends_at_determination_argument: Mapped[float]

    reports_aggregation_strategy: Mapped[AggregationStrategy]

    prize_determinataion_fn: Mapped[SelectionFnEnum]
    prize_determination_argument: Mapped[float]

    created_at: Mapped[CreatedAt]

    members = relationship(ChallengeMember)

    async def ensure_access(
            self,
            session: AsyncSession,
            for_user: User,
            for_role: ChallengeMemberRoleEnum,
    ) -> None:
        stmt = (
            select(self.members)
            .where(ChallengeMember.user_id == for_user.id)
            .where(ChallengeMember.role == for_role)
            .count()
        )
        if not await session.scalar(stmt):
            raise AccessDenied()
        return None
