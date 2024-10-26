from fastapi import APIRouter

from . import (
    auth,
    challenge,
)


router = APIRouter()

router.include_router(auth.router)
router.include_router(challenge.router)
