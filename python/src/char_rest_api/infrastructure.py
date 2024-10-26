from typing import AsyncIterable, Iterable, Annotated, TypeAlias

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from authx import AuthX, AuthXConfig, TokenPayload
from dishka import Provider, provide, Scope, FromComponent, from_context
from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict, BaseSettings
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import Session
from starlette.requests import Request

from char_core.models.user import User


AccessTokenPayload: TypeAlias = TokenPayload


openapi_auth_dep = Depends(OAuth2PasswordBearer(tokenUrl="token"))


class PostgresConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str

    def get_sqlalchemy_url(self, driver: str):
        return "postgresql+{}://{}:{}@{}:{}/{}".format(
            driver,
            self.user,
            self.password,
            self.host,
            self.port,
            self.database,
        )


class AdminConfig(BaseModel):
    secret_key: str
    username: str
    password: str


class RestAPIConfig(BaseModel):
    jwt_secret: str


class CharConfig(BaseSettings):
    postgres: PostgresConfig = None
    rest_api: RestAPIConfig = None
    admin: AdminConfig = None

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_prefix="CHAR__",
        extra="ignore",
    )


class InfrastructureProvider(Provider):
    @provide(scope=Scope.APP)
    def get_config(self) -> CharConfig:
        return CharConfig()

    @provide(scope=Scope.APP)
    def get_postgres_config(
            self,
            config: CharConfig,
    ) -> PostgresConfig:
        if config.postgres is None:
            raise RuntimeError("Postgres configuration not found")

        return config.postgres

    @provide(scope=Scope.APP)
    def get_admin_config(
            self,
            config: CharConfig,
    ) -> AdminConfig:
        if config.admin is None:
            raise RuntimeError("Admin panel configuration not found")

        return config.admin

    @provide(scope=Scope.APP)
    def get_rest_api_config(
            self,
            config: CharConfig,
    ) -> RestAPIConfig:
        if config.rest_api is None:
            raise RuntimeError("Rest API configuration not found.")

        return config.rest_api

    @provide(scope=Scope.APP)
    async def get_async_engine(
            self,
            postgres_config: PostgresConfig,
    ) -> AsyncEngine:
        return create_async_engine(
            postgres_config.get_sqlalchemy_url("asyncpg"),
        )

    @provide(scope=Scope.REQUEST)
    async def get_async_session(
            self,
            engine: AsyncEngine,
    ) -> AsyncIterable[AsyncSession]:
        async with AsyncSession(
            bind=engine,
            expire_on_commit=False,
        ) as session:
            yield session

    @provide(scope=Scope.APP)
    def get_sync_engine(
            self,
            postgres_config: PostgresConfig,
    ) -> Engine:
        return create_engine(
            postgres_config.get_sqlalchemy_url("psycopg"),
        )

    @provide(scope=Scope.REQUEST)
    def get_sync_session(
            self,
            engine: Engine
    ) -> Iterable[Session]:
        with Session(
                bind=engine,
                expire_on_commit=False,
        ) as session:
            yield session

    @provide(scope=Scope.APP)
    def get_authx(
            self,
            rest_api_config: RestAPIConfig,
    ) -> AuthX:
        authx_config = AuthXConfig(
            JWT_ALGORITHM="HS256",
            JWT_SECRET_KEY=rest_api_config.jwt_secret,
        )
        return AuthX(
            config=authx_config,
        )

    request = from_context(provides=Request, scope=Scope.REQUEST)

    @provide(scope=Scope.REQUEST)
    async def get_access_token_payload(
            self,
            request: Request,
            security: AuthX,
    ) -> AccessTokenPayload:
        return await security.access_token_required(request)

    @provide(scope=Scope.REQUEST)
    async def get_user(
            self,
            access_token_payload: AccessTokenPayload,
            session: AsyncSession,
    ) -> User:
        user = await session.get(User, int(access_token_payload.sub))
        if user is None:
            raise HTTPException(
                401,
                detail="Current user does not exists.",
            )
        return user
