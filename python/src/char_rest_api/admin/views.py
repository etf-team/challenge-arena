from sqladmin import ModelView

from char_core.models.user import (
    User,
)
from char_core.models.challenge import ChallengeResult, ChallengeMember, \
    Challenge, Achievement, AchievementAssignation
from char_core.models.space import Space


class UserAdmin(ModelView, model=User):
    column_list = [
        "id",
        "email",
        "phone_number",
        "full_name",
        "description",
        "created_at",
    ]


class SpaceAdmin(ModelView, model=Space):
    column_list = [
        "id",
        "name",
        "description",
        "invitation_token",
        "created_at",
    ]
    form_create_rules = [
        "name",
        "description",
    ]


class AchievementAdmin(ModelView, model=Achievement):
    column_list = [
        "id",
        "name",
        "space",
        "created_at",
    ]


class AchievementAssignationAdmin(ModelView, model=AchievementAssignation):
    column_list = [
        "id",
        "user",
        "challenge",
        "created_at",
    ]


class ChallengeReportAdmin(ModelView, model=ChallengeResult):
    column_list = [
        "id",
        "member",
        "submitted_value",
        "estimatino_value",
        "verification_value",
        "created_at",
    ]
    form_create_rules = [
        "member",
        "submitted_value",
        "estimatino_value",
        "verification_value",
    ]
    form_edit_rules = form_create_rules


class ChallengeMemberAdmin(ModelView, model=ChallengeMember):
    column_list = [
        "id",
        "user",
        "challenge",
        "is_referee",
        "is_participant",
        "is_administrator",
        "cached_aggregated_result",
        "is_winner",
        "created_at",
    ]
    create_template = [
        "user",
        "challenge",
        "is_referee",
        "is_participant",
        "is_administrator",
    ]


class ChallengeAdmin(ModelView, model=Challenge):
    column_list = [
        Challenge.id,
        Challenge.space,
        Challenge.name,
        Challenge.description,
        Challenge.prize,
        Challenge.achievement,
        Challenge.is_verification_required,
        Challenge.is_estimation_required,
        Challenge.starts_at,
        Challenge.ends_at_const,
        Challenge.ends_at_determination_fn,
        Challenge.ends_at_determination_argument,
        Challenge.cached_current_progress,
        Challenge.results_aggregation_strategy,
        Challenge.prize_determination_fn,
        Challenge.prize_determination_argument,
        Challenge.created_at,
        Challenge.members,
        Challenge.results,
    ]

    form_create_rules = [
        "space",
        "name",
        "description",
        "prize",
        "achievement",
        "is_verification_required",
        "is_estimation_required",
        "starts_at",
        "ends_at_const",
        "ends_at_determination_fn",
        "ends_at_determination_argument",
        "results_aggregation_strategy",
        "prize_determination_fn",
        "prize_determination_argument",
    ]
