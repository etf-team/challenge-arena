from __future__ import annotations

from fastapi import HTTPException


class AccessDenied(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=403,
            detail="Access denied",
        )
