from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Iterable, TypeVar

from sqlalchemy import (
    ForeignKey,
    CheckConstraint,
    case,
    func,
    UniqueConstraint,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession

from char_core.exceptions import AccessDenied
from char_core.models.base import Base, IntegerPk, CreatedAt
from char_core.models.user import User

if TYPE_CHECKING:
    from char_core.models.space import Space


_T = TypeVar("_T")


class ChallengeMemberRoleEnum(Enum):
    ANY = "ANY"
    REFREE = "REFREE"
    PARTICIPANT = "PARTICIPANT"
    ADMINISTRATOR = "ADMINISTRATOR"


class AggregationStrategy(Enum):
    SUM = "SUM"
    AVG = "AVG"
    MAX = "MAX"
    MIN = "MIN"

    def evaluate(self, values: list[float]) -> float:
        if self is AggregationStrategy.AVG:
            if not len(values):
                return 0
            return sum(values) / len(values)
        elif self is AggregationStrategy.SUM:
            return sum(values)
        elif self is AggregationStrategy.MAX:
            return max(values)
        elif self is AggregationStrategy.MIN:
            return min(values)
        else:
            raise NotImplementedError(self)


class SelectionFnEnum(Enum):
    HIGHER_THAN = "HIGHER_THAN"
    LESS_THAN = "LESS_THAN"
    HEAD = "HEAD"
    TAIL = "TAIL"

    def evaluate(
            self,
            values: dict[_T, float],
            argument: float,
    ) -> Iterable[_T]:
        # todo: write tests for this stuff
        if self is SelectionFnEnum.HIGHER_THAN:
            return {k: v for k, v in values.items() if v > argument}
        elif self is SelectionFnEnum.LESS_THAN:
            return {k: v for k, v in values.items() if v < argument}
        elif self in (SelectionFnEnum.HEAD, SelectionFnEnum.TAIL):
            orderred = values.items()
            orderred = sorted(orderred, key=lambda x: x[1])
            if self is SelectionFnEnum.HEAD:
                return dict(orderred[:int(argument)])
            else:
                return dict(reversed(orderred)[:int(argument)])
        else:
            raise NotImplementedError(self)

    def evaluate_progress(
            self,
            values: list[float],
            argument: float,
    ):
        if self is SelectionFnEnum.HIGHER_THAN:
            # assumption: start value is 0
            # todo: cover all such progress logic
            numerator = AggregationStrategy.AVG.evaluate(values)
            denominator = argument
            if denominator == 0:
                return 34  # todo: remember and pray :)
            return numerator / denominator * 100
        else:
            raise NotImplementedError(self)


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
    cached_aggregated_result: Mapped[float] = mapped_column(default=0)
    is_referee: Mapped[bool] = mapped_column(default=False)
    is_participant: Mapped[bool] = mapped_column(default=False)
    is_administrator: Mapped[bool] = mapped_column(default=False)
    is_winner: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[CreatedAt]

    user: Mapped[User] = relationship(lazy="selectin")
    challenge: Mapped[Challenge] = relationship(
        back_populates="members",
    )
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "challenge_id",
        ),
    )
    # results: Mapped[list[ChallengeResult]] = relationship(
    #     secondary=lambda: Challenge.__table__,
    #     viewonly=True,
    # )

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
    ends_at_determination_fn: Mapped[SelectionFnEnum | None]
    ends_at_determination_argument: Mapped[float | None]

    cached_current_progress: Mapped[int] = mapped_column(default=0)

    results_aggregation_strategy: Mapped[AggregationStrategy]

    prize_determination_fn: Mapped[SelectionFnEnum]
    prize_determination_argument: Mapped[float]
    finalized_at: Mapped[datetime | None]

    created_at: Mapped[CreatedAt]

    space: Mapped[Space] = relationship(lazy="selectin")
    members: Mapped[list[ChallengeMember]] = relationship(
        back_populates="challenge",
        lazy="selectin",
    )
    results: Mapped[list[ChallengeResult]] = relationship(
        lazy="selectin",
        secondary=lambda: ChallengeMember.__table__,
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
            (cls.starts_at > func.now(),
             ChallengeStateEnum.SCHEDULED.value),
            (cls.cached_current_progress >= 100,
             ChallengeStateEnum.ACTIVE.value),
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

    async def ensure_member_access(
            self,
            user: User,
            administrator: bool = False,
            participant: bool = False,
            refree: bool = False,
    ) -> ChallengeMember:
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

    async def _get_aggregated_results(
            self,
            session: AsyncSession,
    ) -> dict[ChallengeMember, float]:
        all_results = dict()
        for result in self.active_results:
            member: ChallengeMember = await result.awaitable_attrs.member
            all_results.setdefault(member, [])

            if self.is_estimation_required:
                value = result.estimation_value
            else:
                value = result.submitted_value

            all_results[member].append(value)

        result = {
            k: self.results_aggregation_strategy.evaluate(v)
            for k, v in all_results.items()
        }

        # update caches results that displays in rating
        for member, aggregated_result in result.items():
            member.cached_aggregated_result = aggregated_result
        await session.flush()

        return result

    async def _evaluate_is_finished(
            self,
            agg_results: dict[ChallengeMember, float],
    ):
        if self.ends_at_const is not None:
            return self.ends_at_const < datetime.now()

        selected = self.ends_at_determination_fn.evaluate(
            agg_results,
            self.ends_at_determination_argument,
        )
        return bool(selected)

    async def _sync_progress(
            self,
            agg_results: dict[ChallengeMember, float],
    ):
        if await self._evaluate_is_finished(agg_results):
            self.cached_current_progress = 100
        else:
            evaluated = int(
                self.ends_at_determination_fn.evaluate_progress(
                    list(agg_results.values()),
                    self.ends_at_determination_argument,
                )
            )
            assert evaluated < 100
            self.cached_current_progress = evaluated

    async def _finalize(
            self,
            session: AsyncSession,
            agg_results: dict[ChallengeMember, float],
    ):
        # note: concurrent calls wouldn't lead to inconsistante state.
        #  at least I don't see any reasons why it must, if to make
        #  assumption that all reports if frozen. so keep in mind that
        #  this code may be called concurrently, as the rest of code
        #  uses this assumption.  for example, you can't just make
        #  notification mailing here for this reason :)

        self.cached_current_progress = 100
        winners = self.prize_determination_fn.evaluate(
            values=agg_results,
            argument=self.prize_determination_argument,
        )
        for member in winners:
            member.is_winner = True
        self.finalized_at = datetime.now()
        await session.flush((self, *winners))
        await session.commit()

    async def update_lifecycle_state(
            self,
            session: AsyncSession,
    ):
        """
        Update lifecycle state of the challenge.
        :return:
        """

        await session.refresh(self)  # see challenge tests for explanition

        if ChallengeStateEnum(self.state) is ChallengeStateEnum.SCHEDULED:
            return

        if ChallengeStateEnum(self.state) is ChallengeStateEnum.ACTIVE:
            agg_result = await self._get_aggregated_results(
                session=session,
            )
            await session.commit()  # save updated cache
            await self._sync_progress(agg_result)

            # is enough circumstance, state here is already has value finished.

        if ChallengeStateEnum(self.state) is ChallengeStateEnum.FINISHED:
            if self.finalized_at is None:
                agg_result = await self._get_aggregated_results(
                    session=session,
                )
                await session.commit()  # save updated cache
                await self._finalize(
                    session=session,
                    agg_results=agg_result,
                )
            return

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
