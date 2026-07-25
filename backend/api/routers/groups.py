from fastapi import APIRouter, Response

from backend.adapters.content.group_directory import load_group_directory
from backend.api.schemas.group_directory import CastellerGroupDirectorySchema

router = APIRouter()


@router.get("/v1/groups", response_model=CastellerGroupDirectorySchema)
def groups(response: Response, refresh: bool = False) -> CastellerGroupDirectorySchema:
    response.headers["Cache-Control"] = (
        "no-store"
        if refresh
        else "public, s-maxage=86400, stale-while-revalidate=604800"
    )
    return CastellerGroupDirectorySchema.from_domain(load_group_directory())
