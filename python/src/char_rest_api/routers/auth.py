from datetime import datetime
from typing import Annotated

import bcrypt
from authx import AuthX
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, Form

from pydantic import BaseModel, ConfigDict, EmailStr
from char_core.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from char_rest_api.infrastructure import openapi_auth_dep

router = APIRouter()


async def generic_get_token(
        session: AsyncSession,
        security: AuthX,
        username: str,
        password: str,
):
    email = username
    stmt = (
        select(User)
        .filter(User.email == email)
    )
    user: User | None = await session.scalar(stmt)
    exception = HTTPException(401, detail={"message": "Bad credentials"})

    if user is None:
        raise exception

    is_authenticated = bcrypt.checkpw(
        password.encode(),
        user.password_hash.encode(),
    )
    if is_authenticated:
        token = security.create_access_token(uid=str(user.id))
        return {"access_token": token}
    else:
        raise exception


@router.post("/token")
@inject
async def get_token(
        session: FromDishka[AsyncSession],
        security: FromDishka[AuthX],
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
):
    return await generic_get_token(
        session=session,
        security=security,
        username=username,
        password=password,
    )


class TokenRequest(BaseModel):
    username: str
    password: str


@router.post("/token-json")
@inject
async def get_token_json(
        session: FromDishka[AsyncSession],
        security: FromDishka[AuthX],
        payload: TokenRequest,
):
    return await generic_get_token(
        session=session,
        security=security,
        username=payload.username,
        password=payload.password,
    )


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AchievementAssignationDTO(BaseDTO):
    name: str
    space_id: int
    challenge_id: int
    created_at: datetime


class UserDTO(BaseDTO):
    id: int
    full_name: str
    email: str
    achievements_asignations: list[AchievementAssignationDTO]


class Register(BaseModel):
    email: EmailStr
    password: str
    full_name: str


@router.post("/register")
@inject
async def register(
        session: FromDishka[AsyncSession],
        payload: Register,
) -> UserDTO:
    stmt = (
        select(User)
        .where(User.email == payload.email)
    )
    if await session.scalar(stmt):
        raise HTTPException(
            status_code=400,
            detail="Email already in use",
        )

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(payload.password.encode(), salt)

    user = User(
        email=payload.email,
        password_hash=hashed.decode(),
        full_name=payload.full_name,
    )
    session.add(user)
    await session.flush()
    await session.commit()
    await session.refresh(user)
    return UserDTO.model_validate(user)


@router.get(
    "/me",
    dependencies=[openapi_auth_dep],
)
@inject
async def get_protected_resource(
        user: FromDishka[User],
):
    return UserDTO.model_validate(user)
