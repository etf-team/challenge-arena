from sqladmin import ModelView

from char_core.models.user import User


class UserAdmin(ModelView, model=User):
    column_list = [
        "id",
        "email",
        "full_name",
        "description",
        "created_at",
    ]
