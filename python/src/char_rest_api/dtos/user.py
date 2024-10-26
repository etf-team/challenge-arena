from __future__ import annotations

from datetime import datetime

from char_rest_api.dtos.base import BaseDTO


class UserDTO(BaseDTO):
    id: int
    full_name: str
    email: str
    achievements_assignations: list[AchievementAssignationDTO]


class UserFullDTO(UserDTO):
    pass


class AchievementAssignationDTO(BaseDTO):
    id: int
    challenge_id: int
    achievement_id: int
    created_at: datetime
