"""Read-only Jev evaluation: no database writes and no push deliveries.

Run: uv run --env-file .env.jev.local python -m scripts.smoke_jev_news --live-count 5
"""

import argparse
import json
import os
import time

from backend.adapters.ai.jev import JevNewsInterestClassifier
from backend.adapters.content.group_directory import load_group_directory
from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource

EXAMPLES = [
    (
        "Recordatori de l'assaig setmanal dels Verds",
        "L'assaig habitual serà divendres a les 22 h.",
        "low",
    ),
    (
        "La Vella i els Minyons estrenen castells aquesta temporada",
        "Les dues colles milloren els registres de la temporada en una actuació destacada.",
        "medium",
    ),
    (
        "Fita històrica sense precedents al món casteller",
        "S'acaba de descarregar per primer cop a la història una estructura mai assolida. "
        "La colla i l'organització n'han confirmat el resultat.",
        "high",
    ),
    (
        "Nou estudi sobre la participació al món casteller",
        "La CCCC presenta conclusions rellevants sobre els canvis en la participació de les colles.",
        "medium",
    ),
    (
        "Sant Pere i Sant Pau i el Serrallo fan la seva millor actuació per Santa Tecla",
        "La Jove torna a completar el 5de9f, mentre els Xiquets revaliden el 4de9f "
        "i deixen a mitges el 3",
        "high",
    ),
    (
        "Una colla de set signa la millor diada de la seva història",
        "La colla supera la seva millor actuació de tots els temps amb tres castells de set.",
        "high",
    ),
    (
        "La colla descarrega el 3de7 per primer cop a la seva història",
        "Mai abans havia assolit aquest castell; avui l'ha completat per primera vegada.",
        "high",
    ),
    (
        "La colla anuncia el primer intent de 3de7 de la seva història",
        "L'equip tècnic confirma que diumenge provaran aquest castell inèdit per a la colla.",
        "high",
    ),
    (
        "Els Xiquets de Reus completen el primer 3de9f de la temporada",
        "És el primer d'aquest any; ja l'havien descarregat en temporades anteriors.",
        "medium",
    ),
    (
        "Els Castellers de Mallorca intentaran el 3de7.",
        "Tenen previst portar-lo ala Diada de la Colla, el 16 d'octubre vinent a Palma. "
        "Veieu post .",
        "medium",
    ),
    (
        "L’equip de la CBS que farà un especial de castells entrarà avui a la TAP "
        "a localitzar l’espai.",
        "Seran el 4 d'octubre al Concurs per elaborar un programa 60 minuts dedicat als castells.",
        "medium",
    ),
    (
        "Nou article: ‘El Concurs amplia la mirada internacional’.",
        "Més de 300 professionals de més d’un centenar de capçaleres de gairebé una vintena "
        "de països han sol·licitat l'acreditació. Llegiu l'article .",
        "medium",
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-count", type=int, default=0, choices=range(0, 21))
    arguments = parser.parse_args()
    classifier = JevNewsInterestClassifier(
        os.environ["JEV_API_KEY"], os.getenv("JEV_MODEL", "jev-1.13.0")
    )
    groups = load_group_directory().groups
    examples = list(EXAMPLES)
    if arguments.live_count:
        examples.extend(
            (item.display_title, item.summary, None)
            for item in RevistaCastellsHTMLSource().fetch()[: arguments.live_count]
        )
    failures = 0
    for title, summary, expected in examples:
        started = time.monotonic()
        try:
            result = classifier.classify(title, summary, groups, timeout=8)
        except Exception as error:
            print(json.dumps({"title": title, "error": type(error).__name__}, ensure_ascii=False))
            failures += 1
            continue
        failures += int(expected is not None and result.level.value != expected)
        print(
            json.dumps(
                {
                    "title": title,
                    "level": result.level.value,
                    "expected": expected,
                    "groups": sorted(result.group_keys),
                    "confidence": result.confidence,
                    "model": result.model,
                    "criteria": result.criteria_version,
                    "latency_ms": round((time.monotonic() - started) * 1000),
                    "usage": result.usage,
                },
                ensure_ascii=False,
            )
        )
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
