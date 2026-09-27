"""Withdraw an X post from Hora a Hora, for example after a correction or removal request.

Run: python -m backend.jobs.hide_x_post https://x.com/usuari/status/1970000000000000001
"""

from __future__ import annotations

import argparse
import json
import re

from backend.composition.providers import build_database, build_social_post_repository
from backend.config import Settings

_POST_ID = re.compile(r"\d{1,19}")
_STATUS_LINK = re.compile(r"/status/(\d{1,19})(?:[/?#]|$)")


def post_id_from(reference: str) -> str:
    reference = reference.strip()
    if _POST_ID.fullmatch(reference):
        return reference
    match = _STATUS_LINK.search(reference)
    if match is None:
        raise ValueError(f"No és un identificador ni un enllaç de post de X: {reference}")
    return match.group(1)


def hide_once(settings: Settings, reference: str) -> int:
    post_id = post_id_from(reference)
    hidden = build_social_post_repository(build_database(settings)).hide("x", post_id)
    print(json.dumps({"event": "x_post_hidden", "post_id": post_id, "hidden": hidden}), flush=True)
    return 0 if hidden else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Retira un post de X de l'Hora a Hora")
    parser.add_argument("post", help="identificador o enllaç del post")
    return hide_once(Settings.from_env(), parser.parse_args().post)


if __name__ == "__main__":
    raise SystemExit(main())
