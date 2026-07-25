from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from backend.api.dependencies import get_container
from backend.api.schemas.chat import ChatRequestSchema, ChatResponseSchema
from backend.composition.container import ApplicationContainer
from backend.domain.calculator.models import ChatTurn


router = APIRouter()


@router.post("/v1/chat", response_model=ChatResponseSchema)
async def chat(
    payload: ChatRequestSchema,
    request: Request,
    response: Response,
    container: Annotated[ApplicationContainer, Depends(get_container)],
    installation_header: Annotated[str | None, Header(alias="X-Installation-ID")] = None,
) -> ChatResponseSchema:
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"{client_ip}:{installation_header or payload.installation_id}"
    allowed, retry_after = container.rate_limiter.allow(identifier)
    if not allowed:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(status_code=429, detail="Massa consultes. Torna-ho a provar més tard.")

    history = [ChatTurn(role=message.role, content=message.content) for message in payload.messages]
    try:
        result = await container.chat_service.respond(history)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return ChatResponseSchema.from_domain(result)
