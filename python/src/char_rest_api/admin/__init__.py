from datetime import timedelta

from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine

from dishka import AsyncContainer
from fastapi import FastAPI

from char_rest_api.admin.auth_backend import AdminAuthBackend
from char_rest_api.admin import views
from char_rest_api.infrastructure import AdminConfig


async def setup_admin(container: AsyncContainer, app: FastAPI) -> Admin:
    engine = await container.get(AsyncEngine)
    config: AdminConfig = await container.get(AdminConfig)

    admin = Admin(
        app,
        engine=engine,
        authentication_backend=AdminAuthBackend(
            secret_key=config.secret_key,
            username=config.username,
            password=config.password,
            login_duration=timedelta(days=3),
        )
    )

    admin.add_view(views.UserAdmin)
    admin.add_view(views.SpaceAdmin)
    admin.add_view(views.SpaceMemberAdmin)
    admin.add_view(views.AchievementAdmin)
    admin.add_view(views.AchievementAssignationAdmin)
    admin.add_view(views.ChallengeReportAdmin)
    admin.add_view(views.ChallengeMemberAdmin)
    admin.add_view(views.ChallengeAdmin)

    return admin
