import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.api.dependencies import get_container
from backend.composition.container import ApplicationContainer
from backend.observability import log_event

router = APIRouter()
logger = logging.getLogger("horaahora.cron")


def _authorize(container: ApplicationContainer, authorization: str | None) -> None:
    settings = container.settings
    if settings.vercel_env != "production":
        raise HTTPException(status_code=404, detail="No disponible")
    if not settings.cron_secret or authorization != f"Bearer {settings.cron_secret}":
        raise HTTPException(status_code=401, detail="Cron no autoritzat")


@router.get("/internal/cron/hour-by-hour")
def hour_by_hour_cron(
    container: Annotated[ApplicationContainer, Depends(get_container)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, int | str]:
    _authorize(container, authorization)
    if container.notification_coordinator is None:
        log_event(
            logger,
            logging.WARNING,
            "cron_unavailable",
            cron="hour-by-hour",
        )
        return {"status": "unavailable"}
    try:
        result = container.notification_coordinator.run()
    except Exception:
        log_event(
            logger,
            logging.ERROR,
            "cron_failed",
            cron="hour-by-hour",
            exc_info=True,
        )
        raise
    log_event(
        logger,
        logging.ERROR if result.failed else logging.INFO,
        "cron_completed",
        cron="hour-by-hour",
        status=result.status,
        notifications_created=result.notifications_created,
        attempted=result.attempted,
        delivered=result.delivered,
        retried=result.retried,
        invalidated=result.invalidated,
        failed=result.failed,
    )
    return {
        "status": result.status,
        "notifications_created": result.notifications_created,
        "attempted": result.attempted,
        "delivered": result.delivered,
        "retried": result.retried,
        "invalidated": result.invalidated,
        "failed": result.failed,
    }


@router.get("/internal/cron/maintenance")
def maintenance_cron(
    container: Annotated[ApplicationContainer, Depends(get_container)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, int | str]:
    _authorize(container, authorization)
    try:
        notification_counts = container.notification_repository.cleanup()
        rate_limit_count = (
            container.rate_limiter.cleanup_expired()
            if hasattr(container.rate_limiter, "cleanup_expired")
            else 0
        )
    except Exception:
        log_event(
            logger,
            logging.ERROR,
            "cron_failed",
            cron="maintenance",
            exc_info=True,
        )
        raise
    result = {
        "status": "completed",
        "rate_limit_buckets_deleted": rate_limit_count,
        **notification_counts,
    }
    log_event(logger, logging.INFO, "cron_completed", cron="maintenance", **result)
    return result
