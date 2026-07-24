from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.api.dependencies import get_container
from backend.api.schemas.push import PushSubscriptionRequestSchema
from backend.composition.container import ApplicationContainer
from backend.domain.notifications.models import PushSubscriptionRegistration


router = APIRouter()


@router.put(
    "/v1/push-subscriptions/{installation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def register_push_subscription(
    installation_id: str,
    payload: PushSubscriptionRequestSchema,
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> Response:
    if not 1 <= len(installation_id) <= 128:
        raise HTTPException(status_code=422, detail="Identificador d'instal·lació no vàlid")
    container.push_repository.register(
        PushSubscriptionRegistration(
            installation_id=installation_id,
            device_token=payload.device_token,
            app_version=payload.app_version,
            locale=payload.locale,
        ),
        environment=payload.environment or container.settings.apns_environment,
        topic=container.settings.apns_bundle_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/v1/push-subscriptions/{installation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unregister_push_subscription(
    installation_id: str,
    container: Annotated[ApplicationContainer, Depends(get_container)],
    environment: Literal["development", "production"] | None = None,
) -> Response:
    if not 1 <= len(installation_id) <= 128:
        raise HTTPException(status_code=422, detail="Identificador d'instal·lació no vàlid")
    container.push_repository.unregister(
        installation_id,
        environment=environment or container.settings.apns_environment,
        topic=container.settings.apns_bundle_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
