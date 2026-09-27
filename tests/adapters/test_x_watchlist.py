from pathlib import Path

import pytest

from backend.adapters.social.x_watchlist import load_x_watchlist, parse_x_watchlist
from backend.domain.social.models import SocialWatchlist, WatchedAccount

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_accounts_accept_plain_usernames_or_objects_with_their_own_threshold() -> None:
    watchlist = parse_x_watchlist(
        """
        {
          "min_likes": 10,
          "accounts": ["@JoanQuijorna", {"username": "Manelcv", "min_likes": 50}],
          "hashtags": ["#castells", "castellers"]
        }
        """
    )

    assert watchlist == SocialWatchlist(
        min_likes=10,
        accounts=(WatchedAccount("JoanQuijorna"), WatchedAccount("Manelcv", min_likes=50)),
        hashtags=("castells", "castellers"),
    )


def test_the_global_threshold_defaults_to_ten_likes() -> None:
    assert parse_x_watchlist('{"hashtags": ["castells"]}').min_likes == 10


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ("[]", "objecte"),
        ("{", "JSON"),
        ('{"accounts": [], "unknown": 1}', "desconeguts"),
        ('{"min_likes": -1}', "min_likes"),
        ('{"min_likes": true}', "min_likes"),
        ('{"accounts": "JoanQuijorna"}', "llista"),
        ('{"accounts": ["nom amb espais"]}', "usuari"),
        ('{"accounts": ["un_nom_massa_llarg"]}', "usuari"),
        ('{"accounts": [{"username": "Compte", "extra": 1}]}', "desconeguts"),
        ('{"accounts": [{"username": "Compte", "min_likes": "10"}]}', "min_likes"),
        ('{"accounts": ["Compte", "@compte"]}', "Compte duplicat"),
        ('{"hashtags": ["dos mots"]}', "Etiqueta de X no vàlida"),
        ('{"hashtags": ["castells", "#Castells"]}', "Etiqueta duplicada"),
    ],
)
def test_invalid_watchlists_fail_with_a_clear_reason(document: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_x_watchlist(document)


def test_the_versioned_watchlist_is_valid_and_not_empty() -> None:
    watchlist = load_x_watchlist(REPOSITORY_ROOT / "backend/data/x_watchlist.json")

    assert not watchlist.is_empty
    assert watchlist.min_likes == 10
