import traceback
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dishka import FromDishka
from dishka.integrations.fastapi import inject

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from char_core.models.user import (
    User,
)
from char_core.models.challenge import (
    AggregationStrategy,
    SelectionFnEnum,
    ChallengeResult,
    ChallengeMember,
    ChallengeStateEnum,
    Challenge,
)
from char_core.models.space import SpaceMember, Space
from char_rest_api.dtos.challenge import (
    ChallengeDTO,
    ChallengeFullDTO,
    ChallengeResultDTO,
)
from char_rest_api.shortcuts import get_object_or_404


router = APIRouter(
    prefix="/spaces/{space_id}/challenges",
    tags=["Spaces"],
)


class CreateChallenge(BaseModel):
    name: str
    prize: str
    description: str
    achievement_id: int | None
    is_verification_required: bool
    is_estimation_required: bool
    starts_at: datetime
    ends_at_const: datetime | None
    ends_at_determination_fn: SelectionFnEnum | None
    ends_at_determination_argument: float | None
    results_aggregation_strategy: AggregationStrategy
    prize_determination_fn: SelectionFnEnum
    prize_determination_argument: float


@router.post(
    "",
)
@inject
async def create_challenge(
        session: FromDishka[AsyncSession],
        payload: CreateChallenge,
        user: FromDishka[User],
        space_id: int,
) -> ChallengeDTO:
    space: Space = await get_object_or_404(session, Space, space_id)
    await space.ensure_access(
        session=session,
        user=user,
        create_challenge=True,
    )
    challenge = Challenge(
        space_id=space_id,
        **payload.dict(),
    )
    session.add(challenge)
    challenge.members.append(ChallengeMember(
        user_id=user.id,
        is_administrator=True,
        is_referee=True,
        is_participant=True,
    ))
    await session.flush()
    await session.commit()

    return ChallengeDTO.model_validate(challenge)


@router.get(
    "",
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
        spaces = list(spaces)
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
    "/{challenge_id}",
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
    challenge: Challenge = await get_object_or_404(
        session, Challenge, challenge_id)
    assert challenge.space is space
    await challenge.ensure_member_access(
        user=user,
    )
    return ChallengeFullDTO.model_validate(challenge)


@router.post(
    "/{challenge_id}/members"
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
    challenge: Challenge = await get_object_or_404(
        session, Challenge, challenge_id)
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


@router.post(
    "/{challenge_id}/submit-result"
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
    challenge: Challenge = await get_object_or_404(
        session, Challenge, challenge_id)
    assert challenge.space is space
    member = await challenge.ensure_member_access(
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

    try:
        await challenge.update_lifecycle_state(
            session=session,
        )
    except Exception as _:
        print("Error while updating lifecycle state...")
        print(traceback.format_exc())

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
    prize_determination_fn: SelectionFnEnum = None

    def update_model(self, model):
        for i in self.model_fields_set:
            setattr(model, i, getattr(self, i))


@router.patch(
    "/{challenge_id}",
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
    challenge: Challenge = await get_object_or_404(
        session, Challenge, challenge_id)
    assert challenge.space is space
    await challenge.ensure_member_access(
        user=user,
        administrator=True,
    )
    payload.update_model(challenge)
    await session.flush()
    await session.commit()

    return ChallengeFullDTO.model_validate(challenge)
