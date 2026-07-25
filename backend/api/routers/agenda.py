from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from backend.api.dependencies import get_container
from backend.api.schemas.content import AgendaPageSchema, CastellEventSchema
from backend.composition.container import ApplicationContainer

router = APIRouter()


@router.get("/v1/events", response_model=AgendaPageSchema)
def events(
    container: Annotated[ApplicationContainer, Depends(get_container)],
    response: Response,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    group: str | None = None,
    municipality: str | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    refresh: bool = False,
) -> AgendaPageSchema:
    try:
        page = container.agenda_service.list(
            date_from,
            date_to,
            group,
            municipality,
            cursor,
            limit,
            force_refresh=refresh,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="No s'ha pogut actualitzar l'agenda") from error
    response.headers["Cache-Control"] = (
        "no-store" if refresh else "public, s-maxage=300, stale-while-revalidate=86400"
    )
    return AgendaPageSchema(
        items=[CastellEventSchema.from_domain(item) for item in page.items],
        next_cursor=page.next_cursor,
        from_cache=page.from_cache,
        source_status=page.source_status,
    )
