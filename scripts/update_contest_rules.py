from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "backend/data/contest/rules.json"

BASIC_RULES_URL = "https://www.concursdecastells.cat/normes-basiques-2024-cdc"
PLAZA_PROTOCOL_URL = "https://www.concursdecastells.cat/protocol-de-placa-2024-cdc"
CONFIRMED_2026_URL = (
    "https://www.tarragona.cat/cultura/noticies/noticies-2025/"
    "el-concurs-de-castells-mantindra-lordre-en-la-taula-de-puntuacions-pero-"
    "fara-canvis-en-els-punts"
)

CONFIRMED_2026_TEXT = """Canvis confirmats per al Concurs de Castells 2026:
- La taula oficial 2026 incorpora el pilar de set sense folre (Pde7sf).
- El 3 de 7 amb agulla queda puntuat per damunt del 4 de 7 amb agulla.
- En la puntuació final es computen com a màxim dos castells carregats; si una colla aporta tres castells computables, almenys un ha de ser descarregat. La mateixa limitació s'aplica al Rànquing Estrella.
- La diferència de puntuació entre castells carregats i descarregats augmenta respecte de la taula anterior.
- No s'agrupen castells diferents amb una mateixa puntuació i es mantenen les estructures compostes amb agulla.
- La taula de puntuacions 2026 versionada al projecte és la font numèrica autoritativa per als càlculs.

Límits de la font:
- La notícia oficial indicava que altres qüestions operatives encara s'havien de resoldre en la nova normativa.
- A data 2026-08-09 no s'ha localitzat en línia un document complet de Normes bàsiques 2026 ni de Protocol de plaça 2026.
- Cap proposta, preferència d'enquesta o regla de 2024 no es pot presentar com un canvi 2026 confirmat."""


def _text(node: Tag) -> str:
    return " ".join(node.get_text(" ", strip=True).split())


def extract_rule_page(*, source_id: str, year: int, source_url: str, html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one(".col-md-8.body.generica")
    if article is None:
        raise ValueError(f"No s'ha trobat el cos normatiu de {source_url}")
    title_node = article.select_one("h1.title")
    content = article.select_one("div.body.mb20") or article
    lines: list[str] = []
    for node in content.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        if node.name == "p" and node.find_parent("li") is not None:
            continue
        value = _text(node)
        if not value:
            continue
        if node.name == "li":
            value = f"- {value}"
        if not lines or value != lines[-1]:
            lines.append(value)
    if not lines:
        raise ValueError(f"La font normativa {source_url} és buida")
    return {
        "id": source_id,
        "year": year,
        "title": _text(title_node) if title_node else source_id,
        "source_url": source_url,
        "text": "\n".join(lines),
    }


def build_snapshot(*, verified_at: str, session: requests.Session | None = None) -> dict:
    client = session or requests.Session()
    sources = [
        {
            "id": "canvis_confirmats_2026",
            "year": 2026,
            "title": "Canvis confirmats del Concurs de Castells 2026",
            "source_url": CONFIRMED_2026_URL,
            "text": CONFIRMED_2026_TEXT,
        }
    ]
    for source_id, year, source_url in (
        ("normativa_completa_2024", 2024, BASIC_RULES_URL),
        ("protocol_placa_2024", 2024, PLAZA_PROTOCOL_URL),
    ):
        response = client.get(source_url, timeout=30)
        response.raise_for_status()
        sources.append(
            extract_rule_page(
                source_id=source_id,
                year=year,
                source_url=source_url,
                html=response.text,
            )
        )
    return {"verified_at": verified_at, "sources": sources}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenera la instantània versionada de normativa del Concurs."
    )
    parser.add_argument("--verified-at", required=True, help="Data de verificació YYYY-MM-DD")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    snapshot = build_snapshot(verified_at=arguments.verified_at)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
