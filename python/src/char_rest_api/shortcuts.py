from typing import TypeVar, Type
from fastapi import HTTPException

_T = TypeVar("_T")


async def get_object_or_404(session, model_type: Type[_T], ident) -> _T:
    result = await session.get(model_type, ident)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Entity {model_type.__name__} not found",
        )
    return result
