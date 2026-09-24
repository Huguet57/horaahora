import json

import httpx

from backend.adapters.ai.group_aliases import GROUP_ALIASES
from backend.adapters.ai.jev import CRITERIA_VERSION, JevNewsInterestClassifier
from backend.adapters.content.group_directory import load_group_directory
from backend.domain.notifications.interest import group_key


def test_alias_catalog_covers_every_directory_group_without_ambiguous_duplicates():
    directory_keys = {group_key(name) for name in load_group_directory().groups}
    assert set(GROUP_ALIASES) == directory_keys
    owners = {key: key for key in directory_keys}
    for key, aliases in GROUP_ALIASES.items():
        assert aliases, f"Missing aliases for {key}"
        normalized = [group_key(alias) for alias in aliases]
        assert all(normalized)
        assert len(set(normalized)) == len(normalized), key
        assert key not in normalized, f"Canonical name is already sent separately: {key}"
        for alias in normalized:
            assert owners.setdefault(alias, key) == key, f"Ambiguous alias: {alias}"


def test_aliases_include_local_university_and_international_groups():
    expected = {
        "Castellers de Sabadell": "Saballuts",
        "Castellers d'Esplugues": "Cargolins",
        "Castellers de Sant Cugat": "Gausacs",
        "Xiquets de Tarragona": "Matalassers",
        "Colla Castellera de l'Alt Maresme i la Selva Marítima": "Maduixots",
        "Ganàpies de la UAB": "Ganàpies",
        "Castellers of London": "Castellers de Londres",
        "Colla Castellera d’Edinburgh": "Castellers d'Edimburg",
    }
    for name, alias in expected.items():
        assert alias in GROUP_ALIASES[group_key(name)]
    # These labels cannot identify one of the neighbouring/similarly named groups.
    aliases = {group_key(alias) for values in GROUP_ALIASES.values() for alias in values}
    assert aliases.isdisjoint({"barcelona", "valls", "tarragona", "jove", "xiquets"})


def test_jev_sends_catalog_aliases_for_all_groups_and_keeps_unknown_agenda_groups():
    names = load_group_directory().groups + ["Nova Colla de Prova"]
    catalog = {group_key(name): name for name in names}
    requests = []

    def handle(request):
        payload = json.loads(request.content)
        requests.append(payload)
        answers = {
            "interest": {
                "type": "choice",
                "choice": "medium",
                "confidence": 1,
                "probabilities": {"low": 0, "medium": 1, "high": 0},
            }
        }
        for index, key in enumerate(sorted(catalog)):
            question = payload["questions"][f"group_{index}"]
            assert question["instructions"]["colla"] == catalog[key]
            assert question["instructions"]["aliases"] == GROUP_ALIASES.get(key, [])
            answers[f"group_{index}"] = {"type": "noul", "noul": 0}
        return httpx.Response(200, json={"model": "jev-1.13.0", "answers": answers})

    result = JevNewsInterestClassifier("key", transport=httpx.MockTransport(handle)).classify(
        "Saballuts i Gausacs comparteixen diada",
        "També hi participen els Ganàpies.",
        names,
        timeout=1,
    )
    assert len(requests) == 1
    assert len(requests[0]["questions"]) == len(catalog) + 1
    assert result.criteria_version == CRITERIA_VERSION == "castells-interest-v5"
