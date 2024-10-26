from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import run

from char_rest_api import routers
from char_rest_api.admin import setup_admin
from char_rest_api.infrastructure import (
    InfrastructureProvider,
)


def main():
    dependency_providers = (InfrastructureProvider(),)
    container = make_async_container(*dependency_providers)

    @asynccontextmanager
    async def lifespan(current_app: FastAPI):
        await setup_admin(container, current_app)

        yield

        await app.state.dishka_container.close()

    app = FastAPI(
        lifespan=lifespan,
        root_path="/api",
        title="CHAR",
        description="The challenges arena API.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # todo: adjust [sec]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_dishka(container, app)

    app.include_router(routers.router)

    run(
        app,
        host="0.0.0.0",
        port=80,
        forwarded_allow_ips="*",  # todo: adjust [sec]
    )
