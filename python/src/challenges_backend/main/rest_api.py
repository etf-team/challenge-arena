from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from uvicorn import run

from challenges_backend import routers
from challenges_backend.admin import setup_admin
from challenges_backend.infrastructure import InfrastructureProvider


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
    )
    setup_dishka(container, app)

    app.include_router(routers.router)

    run(
        app,
        host="0.0.0.0",
        port=80,
        forwarded_allow_ips="*",  # todo: adjust [sec]
    )
