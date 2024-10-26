from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine

from dishka import AsyncContainer
from fastapi import FastAPI

from char_rest_api.admin.views import UserAdmin


async def setup_admin(container: AsyncContainer, app: FastAPI) -> Admin:
    engine = await container.get(AsyncEngine)
    admin = Admin(app, engine=engine)

    admin.add_view(UserAdmin)

    return admin
