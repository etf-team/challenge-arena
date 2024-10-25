from authx import AuthX
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException

from challenges_backend.infrastructure import RequiredAccessToken


router = APIRouter()


@router.get("/token")
@inject
async def get_token(
        security: FromDishka[AuthX],
        email: str,
        password: str,
):
    is_authenticated = (
            email == "mihailsapovalov05@gmail.com"
            and password == "test"
    )
    if is_authenticated:
        token = security.create_access_token(uid=email)
        return {"access_token": token}
    else:
        raise HTTPException(401, detail={"message": "Bad credentials"})

@router.get(
    "/protected",
)
@inject
async def get_protected_resource(
        _: FromDishka[RequiredAccessToken],
):
    return {"status": "ok"}
