from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from dishka import FromDishka
from dishka.integrations.fastapi import inject

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from char_core.models.challenge import Achievement
from char_core.models.user import (
    User,
)
from char_core.models.space import SpaceMember, Space
from char_rest_api.dtos.space import SpaceDTO, AchievementDTO
from char_rest_api.dtos.base import BaseDTO

router = APIRouter(
    prefix="/spaces",
    tags=["Spaces"],
)


@router.get(
    "",
)
@inject
async def get_all_spaces(
        session: FromDishka[AsyncSession],
        user: FromDishka[User],
) -> list[SpaceDTO]:
    stmt = (
        select(Space)
        .join(SpaceMember,
              and_(SpaceMember.space_id == Space.id,
                   SpaceMember.user_id == user.id))
        .options(selectinload(Space.members))
    )
    results = await session.scalars(stmt)
    return list(map(SpaceDTO.model_validate, results))


@router.get(
    "/{space_id}/achievements",
)
@inject
async def get_all_space_achievements(
        session: FromDishka[AsyncSession],
        user: FromDishka[User],
        space_id: int | Literal["*"],
) -> list[AchievementDTO]:
    stmt = (
        select(Achievement)
        .join(Space,
              Space.id == Achievement.space_id)
        .join(SpaceMember,
              and_(SpaceMember.space_id == Space.id,
                   SpaceMember.user_id == user.id))
    )
    if space_id != "*":
        stmt = stmt.where(Space.id == space_id)

    results = await session.scalars(stmt)
    return [AchievementDTO.model_validate(i)
            for i in results]


class CreateSpace(BaseModel):
    name: str
    description: str = ""


@router.post(
    "",
)
@inject
async def create_space(
        session: FromDishka[AsyncSession],
        payload: CreateSpace,
        user: FromDishka[User],
) -> SpaceDTO:
    space = Space(
        name=payload.name,
        description=payload.description,
    )
    session.add(space)
    space.members.append(SpaceMember(
        space_id=space.id,
        user_id=user.id,
        is_administrator=True,
    ))
    await session.flush()
    await session.commit()
    await session.refresh(space)
    return SpaceDTO.model_validate(space)


class JoinSpaceByToken(BaseDTO):
    invitation_token: str


@router.post(
    "/join-by-token"
)
@inject
async def join_space_by_token(
        session: FromDishka[AsyncSession],
        user: FromDishka[User],
        payload: JoinSpaceByToken,
) -> SpaceDTO:
    stmt = (
        select(Space)
        .where(Space.invitation_token
               == payload.invitation_token)
    )
    space = await session.scalar(stmt)
    member = SpaceMember(
        is_administrator=False,
        user_id=user.id,
    )
    space.members.append(member)
    await session.flush()
    await session.commit()
    await session.refresh(space)

    return SpaceDTO.model_validate(space)
