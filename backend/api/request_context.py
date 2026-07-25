from __future__ import annotations

import logging
import time

from fastapi import Request, Response

from backend.observability import (
    REQUEST_ID_HEADER,
    log_event,
    request_id_context,
    resolve_request_id,
)

logger = logging.getLogger("horaahora.http")


async def request_context_middleware(request: Request, call_next) -> Response:
    request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
    token = request_id_context.set(request_id)
    started = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            log_event(
                logger,
                logging.ERROR,
                "http_request_failed",
                exc_info=True,
                method=request.method,
                path=request.url.path,
            )
            raise

        response.headers[REQUEST_ID_HEADER] = request_id
        status_code = response.status_code
        level = (
            logging.ERROR
            if status_code >= 500
            else logging.WARNING
            if status_code >= 400
            else logging.INFO
        )
        log_event(
            logger,
            level,
            "http_request_completed",
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round((time.perf_counter() - started) * 1_000, 2),
        )
        return response
    finally:
        request_id_context.reset(token)
