import asyncio

from dishka import make_async_container, Scope

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from char_core.models import Challenge
from char_rest_api.infrastructure import InfrastructureProvider


async def daemon():
    while True:
        print("[daemon]: new iteration")
        await asyncio.sleep(1)
        dependency_providers = (InfrastructureProvider(),)
        container = make_async_container(*dependency_providers)
        async with container(scope=Scope.REQUEST) as container:
            session = await container.get(AsyncSession)
            stmt = select(Challenge)
            for challenge in await session.scalars(stmt):
                await challenge.update_lifecycle_state(
                    session=session,
                )


def main():
    asyncio.run(daemon())
