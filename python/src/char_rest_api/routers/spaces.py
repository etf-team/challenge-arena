from fastapi import APIRouter
from pydantic import BaseModel
from dishka import FromDishka
from dishka.integrations.fastapi import inject

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from char_core.models.user import (
    User,
    Space,
    SpaceMember,
)
from char_rest_api.infrastructure import openapi_auth_dep
from char_rest_api.routers.auth import BaseDTO


router = APIRouter(
    prefix="/spaces",
    tags=["Spaces"],
    dependencies=[openapi_auth_dep],
)


class SpaceDTOMember(BaseDTO):
    is_administrator: bool
    space_id: int
    user_id: int


class AchievementDTO(BaseDTO):
    space_id: int
    name: str


class SpaceDTO(BaseDTO):
    name: str
    description: str
    invitation_token: str
    achievements: list[AchievementDTO]


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
