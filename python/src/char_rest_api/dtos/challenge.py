from __future__ import annotations

from datetime import datetime

from pydantic import Field

from char_core.models.challenge import (
    AggregationStrategy,
    SelectionFnEnum,
    ChallengeStateEnum,
)
from char_rest_api.dtos.base import BaseDTO
from char_rest_api.dtos.user import UserDTO


class ChallengeMemberDTO(BaseDTO):
    id: int
    user: UserDTO
    challenge_id: int
    aggregated_result: float = Field(validation_alias="cached_aggregated_result")
    is_winner: bool
    is_referee: bool
    is_participant: bool
    is_administrator: bool
    created_at: datetime


class ChallengeDTO(BaseDTO):
    id: int
    space_id: int
    name: str
    state: ChallengeStateEnum
    description: str
    prize: str | None
    achievement_id: int | None
    is_verification_required: bool
    is_estimation_required: bool
    starts_at: datetime
    current_progress: int = Field(
        validation_alias="cached_current_progress",
    )


class ChallengeFullDTO(ChallengeDTO):
    ends_at_const: datetime | None
    ends_at_determination_fn: SelectionFnEnum | None
    ends_at_determination_argument: float | None
    results_aggregation_strategy: AggregationStrategy
    prize_determination_fn: SelectionFnEnum
    prize_determination_argument: float
    members: list[ChallengeMemberDTO]
    active_results: list[ChallengeResultDTO]


class ChallengeResultDTO(BaseDTO):
    id: int
    member_id: int
    submitted_value: float = Field(description="Assigned by submitter")
    estimation_value: float | None = Field(
        description="May be assigned by refree",
    )
    verification_value: float | None = Field(
        description="May be assigned by administrator",
    )
