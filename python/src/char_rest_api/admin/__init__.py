from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine

from dishka import AsyncContainer
from fastapi import FastAPI


async def setup_admin(container: AsyncContainer, app: FastAPI) -> Admin:
    engine = await container.get(AsyncEngine)
    admin = Admin(app, engine=engine)

    return admin
