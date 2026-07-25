from __future__ import annotations

import json
import logging
from uuid import UUID

from backend.observability import JsonFormatter, log_event, request_id_context
from tests.support.application import make_test_client


def test_json_logs_include_event_context_and_request_id() -> None:
    record = logging.LogRecord(
        name="horaahora.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=12,
        msg="ignored by the structured formatter",
        args=(),
        exc_info=None,
    )
    record.event = "test_failed"
    record.structured_fields = {"component": "tests", "attempt": 2}

    token = request_id_context.set("request-123")
    try:
        payload = json.loads(JsonFormatter().format(record))
    finally:
        request_id_context.reset(token)

    assert payload["level"] == "ERROR"
    assert payload["event"] == "test_failed"
    assert payload["request_id"] == "request-123"
    assert payload["component"] == "tests"
    assert payload["attempt"] == 2
    assert payload["timestamp"].endswith("Z")


def test_log_event_keeps_structured_fields_out_of_the_message(caplog) -> None:
    logger = logging.getLogger("test-observability")

    with caplog.at_level(logging.WARNING, logger=logger.name):
        log_event(logger, logging.WARNING, "delivery_delayed", delivery_id="delivery-1")

    record = caplog.records[-1]
    assert record.getMessage() == "delivery_delayed"
    assert record.event == "delivery_delayed"
    assert record.structured_fields == {"delivery_id": "delivery-1"}


def test_request_id_is_propagated_and_returned() -> None:
    client = make_test_client()

    response = client.get("/health", headers={"X-Request-ID": "request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-123"


def test_invalid_request_id_is_replaced_with_a_uuid() -> None:
    client = make_test_client()

    response = client.get("/health", headers={"X-Request-ID": "contains spaces"})

    assert response.status_code == 200
    assert str(UUID(response.headers["X-Request-ID"])) == response.headers["X-Request-ID"]
