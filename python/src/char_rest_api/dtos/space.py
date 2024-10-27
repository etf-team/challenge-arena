from char_rest_api.dtos.base import BaseDTO


class SpaceMemberDTO(BaseDTO):
    id: int
    is_administrator: bool
    space_id: int
    user_id: int


class AchievementDTO(BaseDTO):
    id: int
    space_id: int
    name: str


class SpaceDTO(BaseDTO):
    id: int
    name: str
    description: str
    invitation_token: str
    achievements: list[AchievementDTO]
