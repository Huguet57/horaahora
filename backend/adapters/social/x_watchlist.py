"""Parse the configurable list of X accounts and hashtags followed by Hora a Hora."""

import json
import re
from pathlib import Path

from backend.domain.social.models import SocialWatchlist, WatchedAccount

DEFAULT_MIN_LIKES = 10
_USERNAME = re.compile(r"[A-Za-z0-9_]{1,15}")
_HASHTAG = re.compile(r"\w{1,100}")
_DOCUMENT_FIELDS = {"min_likes", "accounts", "hashtags"}
_ACCOUNT_FIELDS = {"username", "min_likes"}


def load_x_watchlist(path: Path) -> SocialWatchlist:
    return parse_x_watchlist(path.read_text(encoding="utf-8"))


def parse_x_watchlist(document: str) -> SocialWatchlist:
    try:
        data = json.loads(document)
    except json.JSONDecodeError as error:
        raise ValueError("La llista de seguiment de X no és JSON vàlid") from error
    if not isinstance(data, dict):
        raise ValueError("La llista de seguiment de X ha de ser un objecte JSON")
    _reject_unknown_fields(data, _DOCUMENT_FIELDS)
    accounts = tuple(_account(value) for value in _list(data, "accounts"))
    hashtags = tuple(_hashtag(value) for value in _list(data, "hashtags"))
    _reject_duplicates([account.username for account in accounts], "Compte duplicat")
    _reject_duplicates(list(hashtags), "Etiqueta duplicada")
    return SocialWatchlist(
        min_likes=_threshold(data.get("min_likes", DEFAULT_MIN_LIKES)),
        accounts=accounts,
        hashtags=hashtags,
    )


def _account(value: object) -> WatchedAccount:
    if isinstance(value, str):
        return WatchedAccount(_username(value))
    if not isinstance(value, dict):
        raise ValueError("Cada compte ha de ser un nom d'usuari o un objecte")
    _reject_unknown_fields(value, _ACCOUNT_FIELDS)
    min_likes = value.get("min_likes")
    return WatchedAccount(
        _username(value.get("username")),
        min_likes=None if min_likes is None else _threshold(min_likes),
    )


def _username(value: object) -> str:
    username = value.removeprefix("@") if isinstance(value, str) else ""
    if not _USERNAME.fullmatch(username):
        raise ValueError(f"Nom d'usuari de X no vàlid: {value!r}")
    return username


def _hashtag(value: object) -> str:
    hashtag = value.removeprefix("#") if isinstance(value, str) else ""
    if not _HASHTAG.fullmatch(hashtag):
        raise ValueError(f"Etiqueta de X no vàlida: {value!r}")
    return hashtag


def _threshold(value: object) -> int:
    # bool is an int subclass: reject it explicitly instead of reading true as 1.
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("min_likes ha de ser un enter no negatiu")
    return value


def _list(data: dict, name: str) -> list:
    values = data.get(name, [])
    if not isinstance(values, list):
        raise ValueError(f"{name} ha de ser una llista")
    return values


def _reject_unknown_fields(data: dict, allowed: set[str]) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(f"Camps desconeguts a la llista de seguiment de X: {', '.join(unknown)}")


def _reject_duplicates(values: list[str], problem: str) -> None:
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key in seen:
            raise ValueError(f"{problem} a la llista de seguiment de X: {value}")
        seen.add(key)
