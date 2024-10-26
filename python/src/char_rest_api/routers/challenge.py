from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from dishka import FromDishka
from dishka.integrations.fastapi import inject

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from char_core.models.user import Challenge
from char_rest_api.routers.auth import BaseDTO


router = APIRouter(
    prefix="/challenges",
    tags=["Challenges"],
)


class CreateChallenge(BaseModel):
    name: str
    prize: str


class ChallengeDTO(BaseDTO):
    name: str
    prize: str


@router.post(
    "/",
)
@inject
async def create_challenge(
        session: FromDishka[AsyncSession],
        payload: CreateChallenge,
):
    challenge = Challenge(
        name=payload.name,
        prize=payload.prize,
    )
    session.add(challenge)
    await session.flush()
    await session.commit()

    return ChallengeDTO.model_validate(challenge)


@router.get(
    "/",
)
@inject
async def get_challenges(
        session: FromDishka[AsyncSession],
):
    stmt = select(Challenge)
    challenges = await session.scalars(stmt)

    return [
        ChallengeDTO.model_validate(i)
        for i in challenges
    ]


class ChallengeFullDTO(BaseDTO):
    name: str
    prize: str


@router.get(
    "/challenges/{challenge_id}",
)
@inject
async def get_full_challenge(
        session: FromDishka[AsyncSession],
        challenge_id: int,
):
    challenge = await session.get(Challenge, challenge_id)
    return ChallengeFullDTO.model_validate(challenge)


class EditSession(BaseModel):
    name: str = None
    prize: str = None

    def update_model(self, model):
        for i in self.model_fields_set:
            setattr(model, i, getattr(self, i))


@router.patch(
    "/challenges/{challenge_id}",
)
@inject
async def edit_challenge(
        session: FromDishka[AsyncSession],
        payload: EditSession,
        challenge_id: int,
):
    challenge = await session.get(Challenge, challenge_id)

    payload.update_model(challenge)
    await session.flush()
    await session.commit()

    return ChallengeFullDTO.model_validate(challenge)
