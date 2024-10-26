from sqladmin import ModelView

from char_core.models.user import (
    User,
    Space,
    Achievement,
    AchievementAssignation,
    ChallengeResult,
    ChallengeMember,
    Challenge,
)


class UserAdmin(ModelView, model=User):
    column_list = [
        "id",
        "email",
        "full_name",
        "description",
        "created_at",
    ]


class SpaceAdmin(ModelView, model=Space):
    column_list = [
        "id",
        "name",
        "invitation_token",
        "created_at",
    ]
    form_create_rules = [
        "name",
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
    form_edit_rules = [
        "member",
        "submitted_value",
        "estimatino_value",
        "verification_value",
    ]


class ChallengeMemberAdmin(ModelView, model=ChallengeMember):
    column_list = [
        "id",
        "user",
        "challenge",
        "is_owner",
        "is_referee",
        "is_participant",
        "is_administrator",
        "created_at",
    ]


class ChallengeAdmin(ModelView, model=Challenge):
    column_list = [
        "id",
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
        "cached_current_progress",
        "results_aggregation_strategy",
        "prize_determination_fn",
        "prize_determination_argument",
        "created_at",
        "members",
        "results",
    ]

    form_create_rules = [
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
        "prize_determinataion_fn",
        "prize_determination_argument",
    ]
