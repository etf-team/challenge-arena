from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from dishka import FromDishka
from dishka.integrations.fastapi import inject

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from char_core.models.user import (
    Challenge,
    User,
    ChallengeMember, AggregationStrategy, SelectionFnEnum, ChallengeResult,
    ChallengeStateEnum, SpaceMember, Space,
)
from char_rest_api.infrastructure import openapi_auth_dep
from char_rest_api.routers.auth import BaseDTO, UserDTO
from char_rest_api.shortcuts import get_object_or_404

router = APIRouter(
    prefix="/spaces",
    tags=["Spaces"],
    dependencies=[openapi_auth_dep],
)


class CreateChallenge(BaseModel):
    name: str
    prize: str
    description: str
    achievement_id: int | None
    is_verification_required: bool
    is_estimation_required: bool
    starts_at: datetime
    ends_at_const: datetime
    ends_at_determination_fn: SelectionFnEnum
    ends_at_determination_argument: float
    results_aggregation_strategy: AggregationStrategy
    prize_determinataion_fn: SelectionFnEnum
    prize_determination_argument: float


class AchievementDTO(BaseDTO):
    name: str
    space_id: int


class ChallengeMemberDTO(BaseDTO):
    id: int
    user: UserDTO
    challenge_id: int
    is_referee: bool
    is_participant: bool
    is_administrator: bool
    created_at: datetime


class ChallengeDTO(BaseDTO):
    space_id: int
    name: str
    state: ChallengeStateEnum
    description: str
    prize: str | None
    achievement_id: int | None
    is_verification_required: bool
    is_estimation_required: bool
    starts_at: datetime
    current_progress: int = Field(
        validation_alias="cached_current_progress",
    )


class ChallengeFullDTO(ChallengeDTO):
    ends_at_const: datetime | None
    ends_at_determination_fn: SelectionFnEnum
    ends_at_determination_argument: float
    results_aggregation_strategy: AggregationStrategy
    prize_determinataion_fn: SelectionFnEnum
    members: list[ChallengeMemberDTO]


@router.post(
    "/{space_id}/challenges",
)
@inject
async def create_challenge(
        session: FromDishka[AsyncSession],
        payload: CreateChallenge,
        user: FromDishka[User],
        space_id: int,
) -> ChallengeDTO:
    challenge = Challenge(
        space_id=space_id,
        **payload.dict(),
    )
    session.add(challenge)
    challenge.members.append(ChallengeMember(
        user_id=user.id,
        is_administrator=True,
        is_participant=True,
    ))
    await session.flush()
    await session.commit()

    return ChallengeDTO.model_validate(challenge)


@router.get(
    "/{space_id}/challenges",
)
@inject
async def get_challenges(
        session: FromDishka[AsyncSession],
        user: FromDishka[User],
        space_id: int | Literal["*"],
        state: ChallengeStateEnum = None,
) -> list[ChallengeDTO]:
    if space_id == "*":
        stmt = (
            select(Space)
            .join(SpaceMember, and_(SpaceMember.space_id == Space.id,
                                    SpaceMember.user_id == user.id))
        )
        spaces = await session.scalars(stmt)

    else:
        space: Space = await get_object_or_404(session, Space, space_id)
        spaces = [space]

    for space in spaces:
        await space.ensure_access(
            session=session,
            user=user,
            edit=False,
        )

    stmt = (select(Challenge)
            .where(Challenge.space_id.in_({i.id for i in spaces})))
    if state is not None:
        stmt = stmt.where(Challenge.state == state.value)

    challenges = await session.scalars(stmt)

    return [
        ChallengeDTO.model_validate(i)
        for i in challenges
    ]


@router.get(
    "{space_id}/challenges/{challenge_id}",
)
@inject
async def get_full_challenge(
        session: FromDishka[AsyncSession],
        user: FromDishka[User],
        challenge_id: int,
        space_id: int,
) -> ChallengeFullDTO:
    space: Space = await get_object_or_404(session, Space, space_id)
    await space.ensure_access(
        session=session,
        user=user,
        edit=False,
    )
    challenge: Challenge = await get_object_or_404(session, Challenge, challenge_id)
    assert challenge.space is space
    await challenge.ensure_access(
        user=user,
        just_view=True,
    )
    return ChallengeFullDTO.model_validate(challenge)


@router.post(
    "{space_id}/challenges/{challenge_id}/members"
)
@inject
async def join_challenge(
        session: FromDishka[AsyncSession],
        user: FromDishka[User],
        challenge_id: int,
        space_id: int,
) -> ChallengeFullDTO:
    space: Space = await get_object_or_404(session, Space, space_id)
    await space.ensure_access(
        session=session,
        user=user,
        edit=False,
    )
    challenge: Challenge = await get_object_or_404(session, Challenge, challenge_id)
    assert challenge.space is space
    stmt = (select(ChallengeMember)
            .where(ChallengeMember.challenge_id == challenge.id)
            .where(ChallengeMember.user_id == user.id))
    existing_member = await session.scalar(stmt)

    if existing_member is not None:
        raise HTTPException(
            status_code=400,
            detail="You already joined the challenge.",
        )
    member = ChallengeMember(
        user=user,
        challenge=challenge,
        is_participant=True,
    )
    session.add(member)
    await session.flush()
    await session.commit()
    return ChallengeFullDTO.model_validate(challenge)


class SubmitChallengeResult(BaseModel):
    submitted_value: float


class ChallengeResultDTO(BaseDTO):
    id: int
    member_id: int
    submitted_value: float = Field(description="Assigned by submitter")
    estimation_value: float | None = Field(
        description="May be assigned by refree",
    )
    verification_value: float | None = Field(
        description="May be assigned by administrator",
    )


@router.post(
    "{space_id}/challenges/{challenge_id}/submit-result"
)
@inject
async def submit_challenge_result(
        session: FromDishka[AsyncSession],
        user: FromDishka[User],
        challenge_id: int,
        space_id: int,
        payload: SubmitChallengeResult,
) -> ChallengeResultDTO:
    space: Space = await get_object_or_404(session, Space, space_id)
    await space.ensure_access(
        session=session,
        user=user,
        edit=False,
    )
    challenge: Challenge = await get_object_or_404(session, Challenge, challenge_id)
    assert challenge.space is space
    member = await challenge.ensure_access(
        user=user,
        participant=True,
    )
    result = ChallengeResult(
        member_id=member.id,
        submitted_value=payload.submitted_value,
    )
    session.add(result)
    await session.flush()
    await session.commit()
    return ChallengeResultDTO.model_validate(result)


class EditChallenge(BaseModel):
    name: str = None
    description: str = None
    prize: str | None = None
    achievement_id: int | None = None
    is_verification_required: bool = None
    is_estimation_required: bool = None
    starts_at: datetime = None
    ends_at_const: datetime | None = None
    ends_at_determination_fn: SelectionFnEnum = None
    ends_at_determination_argument: float = None
    results_aggregation_strategy: AggregationStrategy = None
    prize_determinataion_fn: SelectionFnEnum = None


    def update_model(self, model):
        for i in self.model_fields_set:
            setattr(model, i, getattr(self, i))


@router.patch(
    "{space_id}/challenges/{challenge_id}",
)
@inject
async def edit_challenge(
        session: FromDishka[AsyncSession],
        user: FromDishka[User],
        payload: EditChallenge,
        challenge_id: int,
        space_id: int,
) -> ChallengeFullDTO:
    space: Space = await get_object_or_404(session, Space, space_id)
    await space.ensure_access(
        session=session,
        user=user,
        edit=False,
    )
    challenge: Challenge = await get_object_or_404(session, Challenge, challenge_id)
    assert challenge.space is space
    await challenge.ensure_access(
        user=user,
        administrator=True,
    )
    payload.update_model(challenge)
    await session.flush()
    await session.commit()

    return ChallengeFullDTO.model_validate(challenge)
