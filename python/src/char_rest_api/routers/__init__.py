from fastapi import APIRouter

from . import (
    auth,
    spaces,
    challenges,
)


router = APIRouter()

router.include_router(auth.router)
router.include_router(spaces.router)
router.include_router(challenges.router)
