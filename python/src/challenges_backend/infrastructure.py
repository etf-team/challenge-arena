from typing import AsyncIterable, Iterable

from authx import AuthX, AuthXConfig, TokenPayload
from dishka import Provider, provide, Scope
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


RequiredAccessToken = TokenPayload


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


class ChallengesConfig(BaseSettings):
    postgres: PostgresConfig = None
    rest_api: RestAPIConfig = None
    admin: AdminConfig = None

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_prefix="CLOYT__",
        toml_file="cloyt.toml",
        extra="ignore",
    )


class InfrastructureProvider(Provider):
    @provide(scope=Scope.APP)
    def get_config(self) -> ChallengesConfig:
        return ChallengesConfig()

    @provide(scope=Scope.APP)
    def get_postgres_config(
            self,
            config: ChallengesConfig,
    ) -> PostgresConfig:
        if config.postgres is None:
            raise RuntimeError("Postgres configuration not found")

        return config.postgres

    @provide(scope=Scope.APP)
    def get_admin_config(
            self,
            config: ChallengesConfig,
    ) -> AdminConfig:
        if config.admin is None:
            raise RuntimeError("Admin panel configuration not found")

        return config.admin

    @provide(scope=Scope.APP)
    def get_rest_api_config(
            self,
            config: RestAPIConfig,
    ) -> RestAPIConfig:
        if config.daemon is None:
            raise RuntimeError("Rest API configuration not found.")

        return config.daemon

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
        async with AsyncSession(bind=engine) as session:
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
        with Session(bind=engine, expire_on_commit=False) as session:
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

    @provide(scope=Scope.REQUEST)
    async def require_access_token(
            self,
            request: Request,
            security: AuthX,
    ) -> RequiredAccessToken:
        return await security.access_token_required(request)
