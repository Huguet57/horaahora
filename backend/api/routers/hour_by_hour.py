from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies import get_container
from backend.api.schemas.content import HourByHourItemSchema, HourByHourPageSchema
from backend.composition.container import ApplicationContainer


router = APIRouter()


@router.get("/v1/hour-by-hour", response_model=HourByHourPageSchema)
def hour_by_hour(
    container: Annotated[ApplicationContainer, Depends(get_container)],
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    refresh: bool = False,
) -> HourByHourPageSchema:
    try:
        page = container.hour_by_hour_service.list(cursor, limit, force_refresh=refresh)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=502, detail="No s'ha pogut actualitzar Hora a Hora"
        ) from error
    return HourByHourPageSchema(
        items=[HourByHourItemSchema.from_domain(item) for item in page.items],
        next_cursor=page.next_cursor,
        from_cache=page.from_cache,
    )
