from fastapi import APIRouter

from char_rest_api.infrastructure import openapi_auth_dep
from . import (
    auth,
    space,
    challenge,
)

router = APIRouter()

outer_router = APIRouter()
outer_router.include_router(auth.router)

inner_router = APIRouter(
    dependencies=[openapi_auth_dep],
)
inner_router.include_router(space.router)
inner_router.include_router(challenge.router)

router.include_router(outer_router)
router.include_router(inner_router)
