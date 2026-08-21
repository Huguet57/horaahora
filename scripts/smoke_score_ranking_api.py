#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SmokeCase:
    name: str
    question: str
    expected_intent: str
    required_tokens: tuple[str, ...]
    forbidden_tokens: tuple[str, ...] = ()
    expected_presentation_type: str | None = None
    expected_rows: tuple[str, ...] = ()
    expected_outcome: str | None = None


CASES = (
    SmokeCase(
        "highest",
        "Quin és el castell que dona més punts?",
        "contest_info",
        ("3de10sm", "6205", "7475"),
        expected_presentation_type="score_ranking",
        expected_rows=("3de10sm",),
        expected_outcome="both",
    ),
    SmokeCase(
        "lowest",
        "Quin és el castell que dona menys punts?",
        "contest_info",
        ("2de6", "250", "300"),
        expected_presentation_type="score_ranking",
        expected_rows=("2de6",),
        expected_outcome="both",
    ),
    SmokeCase(
        "top-five",
        "Quins són els cinc primers castells del rànquing de puntuacions 2026?",
        "contest_info",
        ("3de10sm", "4de10sm", "2de10fmp", "Pde7sf", "3de9sf"),
        expected_presentation_type="score_ranking",
        expected_rows=("3de10sm", "4de10sm", "2de10fmp", "Pde7sf", "3de9sf"),
        expected_outcome="both",
    ),
    SmokeCase(
        "position",
        "En quina posició del rànquing està el Pde7sf i quants punts dona?",
        "contest_info",
        ("Pde7sf", "5280", "6360"),
        expected_presentation_type="score_ranking",
        expected_rows=("Pde7sf",),
        expected_outcome="both",
    ),
    SmokeCase(
        "neighbors",
        "Quins castells hi ha just per sobre i per sota del Pde7sf?",
        "contest_info",
        ("2de10fmp", "3de9sf"),
        expected_presentation_type="score_ranking",
        expected_rows=("2de10fmp", "Pde7sf", "3de9sf"),
        expected_outcome="both",
    ),
    SmokeCase(
        "loaded-ranking",
        "Quin és el castell més puntuat si només queda carregat?",
        "contest_info",
        ("3de10sm", "6205"),
        ("7475",),
        expected_presentation_type="score_ranking",
        expected_rows=("3de10sm",),
        expected_outcome="loaded",
    ),
    SmokeCase(
        "unloaded-ranking",
        "Quin és el castell més puntuat descarregat?",
        "contest_info",
        ("3de10sm", "7475"),
        ("6205",),
        expected_presentation_type="score_ranking",
        expected_rows=("3de10sm",),
        expected_outcome="unloaded",
    ),
    SmokeCase(
        "existing-lookup",
        "Quants punts dona el 5de9f descarregat?",
        "lookup",
        ("5de9f", "3125"),
    ),
)


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", without_accents)


def _post_question(
    base_url: str,
    case: SmokeCase,
    *,
    vercel_auth: bool = False,
) -> dict[str, object]:
    installation_id = f"score-ranking-smoke-{case.name}-{uuid.uuid4()}"
    payload = {
        "conversation_id": str(uuid.uuid4()),
        "installation_id": installation_id,
        "locale": "ca-ES",
        "ruleset": "concurs-2026",
        "messages": [{"role": "user", "content": case.question}],
    }
    encoded_payload = json.dumps(payload)
    if vercel_auth:
        result = subprocess.run(
            [
                "vercel",
                "curl",
                "/v1/chat",
                "--deployment",
                base_url,
                "--",
                "--silent",
                "--show-error",
                "--request",
                "POST",
                "--header",
                "Content-Type: application/json",
                "--header",
                f"X-Installation-ID: {installation_id}",
                "--data-binary",
                encoded_payload,
            ],
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"{case.name}: vercel curl failed: {result.stderr.strip()}")
        response_payload = json.loads(result.stdout)
        if not isinstance(response_payload, dict):
            raise AssertionError(f"{case.name}: real API response is not an object")
        return response_payload

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/chat",
        data=encoded_payload.encode(),
        headers={"Content-Type": "application/json", "X-Installation-ID": installation_id},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=75) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        body = error.read().decode(errors="replace")
        raise AssertionError(f"{case.name}: HTTP {error.code}: {body}") from error


def _validate(case: SmokeCase, response: dict[str, object]) -> str:
    intent = response.get("intent")
    if intent != case.expected_intent:
        raise AssertionError(
            f"{case.name}: expected intent {case.expected_intent!r}, received {intent!r}"
        )
    reply = response.get("reply")
    if not isinstance(reply, str):
        raise AssertionError(f"{case.name}: response has no textual reply")
    normalized_reply = _normalized(reply)
    missing = [
        token for token in case.required_tokens if _normalized(token) not in normalized_reply
    ]
    forbidden = [token for token in case.forbidden_tokens if _normalized(token) in normalized_reply]
    if missing or forbidden:
        raise AssertionError(
            f"{case.name}: missing={missing}, forbidden={forbidden}, reply={reply!r}"
        )
    if case.expected_presentation_type is not None:
        presentation = response.get("presentation")
        if not isinstance(presentation, dict):
            raise AssertionError(f"{case.name}: response has no structured presentation")
        if presentation.get("type") != case.expected_presentation_type:
            raise AssertionError(
                f"{case.name}: expected presentation {case.expected_presentation_type!r}, "
                f"received {presentation.get('type')!r}"
            )
        if presentation.get("outcome") != case.expected_outcome:
            raise AssertionError(
                f"{case.name}: expected outcome {case.expected_outcome!r}, "
                f"received {presentation.get('outcome')!r}"
            )
        rows = presentation.get("rows")
        if not isinstance(rows, list):
            raise AssertionError(f"{case.name}: presentation rows are missing")
        notations = tuple(row.get("notation") for row in rows if isinstance(row, dict))
        if notations != case.expected_rows:
            raise AssertionError(
                f"{case.name}: expected rows {case.expected_rows!r}, received {notations!r}"
            )
    return reply


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the real score-ranking chat API.")
    parser.add_argument("base_url", help="Deployed Preview or production base URL")
    parser.add_argument(
        "--vercel-auth",
        action="store_true",
        help="Use `vercel curl` to authenticate against a protected Preview",
    )
    args = parser.parse_args()

    for case in CASES:
        reply = _validate(
            case,
            _post_question(args.base_url, case, vercel_auth=args.vercel_auth),
        )
        print(f"PASS {case.name}: {reply}")

    print(f"PASS all {len(CASES)} real API score-ranking cases")


if __name__ == "__main__":
    main()
