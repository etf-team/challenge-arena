from typing import Annotated

import bcrypt
from authx import AuthX
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, Depends, Form

from pydantic import BaseModel, ConfigDict
from char_core.models.user import User
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.post("/token")
@inject
async def get_token(
        session: FromDishka[AsyncSession],
        security: FromDishka[AuthX],
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
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


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserDTO(BaseDTO):
    id: int
    full_name: str
    email: str


@router.post("/register")
@inject
async def register(
        session: FromDishka[AsyncSession],
        email: str,
        password: str,
        full_name: str,
) -> UserDTO:
    stmt = (
        select(User)
        .where(User.email == email)
    )
    if await session.scalar(stmt):
        raise HTTPException(
            status_code=400,
            detail="Email already in use",
        )

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)

    user = User(
        email=email,
        password_hash=hashed.decode(),
        full_name=full_name,
    )
    session.add(user)
    await session.flush()
    await session.commit()
    return UserDTO.model_validate(user)


openapi_auth_dep = Depends(OAuth2PasswordBearer(tokenUrl="token"))


@router.get(
    "/me",
    dependencies=[openapi_auth_dep],
)
@inject
async def get_protected_resource(
        user: FromDishka[User],
):
    return UserDTO.model_validate(user)
