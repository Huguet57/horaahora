from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_container
from backend.composition.container import ApplicationContainer

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> dict[str, str]:
    if not container.database.is_ready():
        raise HTTPException(status_code=503, detail="La base de dades no està disponible")
    return {"status": "ready"}
