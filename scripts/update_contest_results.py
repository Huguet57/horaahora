from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://www.concursdecastells.cat"
SOURCE_INDEX = f"{BASE_URL}/edicions-anteriors-cdc"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "backend/data/contest/previous_results.json"
EXPECTED_EDITION_COUNT = 30

RESULT_BY_CLASS = {
    "bg-verde": "descarregat",
    "bg-naranja": "carregat",
    "bg-rojo": "intent_desmuntat",
    "bg-grana": "intent",
    "bg-default": "sense_actuació",
}


def _text(node: Tag) -> str:
    return " ".join(node.get_text(" ", strip=True).split())


def _modern_round(cell: Tag) -> dict[str, Any]:
    marker = cell.find("span") or cell
    marker_classes = set(marker.get("class", []))
    result = next(
        (label for css_class, label in RESULT_BY_CLASS.items() if css_class in marker_classes),
        "desconegut",
    )
    penalized = cell.select_one(".penalizado")
    return {
        "notation": _text(cell),
        "result": result,
        "counted": "bg-black" in cell.get("class", []),
        "penalty": penalized.get("title") if penalized else None,
    }


def _parse_modern_table(table: Tag) -> tuple[list[str], list[dict[str, Any]]]:
    classification: list[dict[str, Any]] = []
    maximum_rounds = 0
    for row in table.select("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) < 3 or cells[0].name == "th":
            continue
        round_cells = cells[2:-1]
        maximum_rounds = max(maximum_rounds, len(round_cells))
        classification.append(
            {
                "position": _text(cells[0]),
                "group": _text(cells[1]),
                "rounds": [_modern_round(cell) for cell in round_cells],
                "points": _text(cells[-1]),
            }
        )
    columns = (
        ["Posició", "Colla"]
        + [f"Ronda {index}" for index in range(1, maximum_rounds + 1)]
        + ["Punts"]
    )
    return columns, classification


def _parse_historical_table(table: Tag) -> tuple[list[str], list[dict[str, Any]]]:
    rows = table.select("tr")
    columns: list[str] = []
    classification: list[dict[str, Any]] = []
    for row in rows:
        cells = row.find_all(["th", "td"], recursive=False)
        values = [_text(cell) for cell in cells]
        if not values:
            continue
        if not columns and any(cell.name == "th" for cell in cells):
            columns = values
            continue
        classification.append({"cells": values})
    if not columns:
        raise ValueError("La taula històrica no conté cap capçalera")
    return columns, classification


def parse_edition_page(*, year: int, source_url: str, html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one(".col-md-8.body.generica")
    if article is None:
        raise ValueError(f"No s'ha trobat el cos de l'edició {year}")
    content = article.select_one("div.body.mb20")
    if content is None:
        raise ValueError(f"No s'ha trobat el contingut de l'edició {year}")
    title_node = article.select_one("h1.title")
    if title_node is None:
        raise ValueError(f"No s'ha trobat el títol de l'edició {year}")
    title = _text(title_node)
    note = " ".join(_text(paragraph) for paragraph in content.find_all("p", recursive=False))
    tables = [table for table in content.find_all("table") if table.select_one("tr")]

    if not tables:
        if year != 2020 or "no es va celebrar" not in note.lower():
            raise ValueError(f"L'edició {year} no conté cap classificació reconeguda")
        return {
            "year": year,
            "title": title,
            "status": "cancelled",
            "source_url": source_url,
            "note": note,
            "columns": [],
            "classification": [],
        }

    modern_tables = [table for table in tables if table.select_one("td.td-datos")]
    if modern_tables:
        if len(modern_tables) != 1:
            raise ValueError(f"L'edició {year} conté més d'una classificació moderna")
        columns, classification = _parse_modern_table(modern_tables[0])
    else:
        if len(tables) != 1:
            raise ValueError(f"L'edició {year} conté més d'una classificació històrica")
        columns, classification = _parse_historical_table(tables[0])
    if not classification:
        raise ValueError(f"La classificació de l'edició {year} és buida")
    return {
        "year": year,
        "title": title,
        "status": "held",
        "source_url": source_url,
        "note": note,
        "columns": columns,
        "classification": classification,
    }


def discover_editions(html: str) -> list[tuple[int, str]]:
    soup = BeautifulSoup(html, "html.parser")
    found: dict[int, str] = {}
    pattern = re.compile(r"^/concurs-(\d{4})(?:-1)?-cdc$")
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        match = pattern.match(href)
        if match:
            found[int(match.group(1))] = f"{BASE_URL}{href}"
    editions = sorted(found.items(), reverse=True)
    if len(editions) != EXPECTED_EDITION_COUNT:
        raise ValueError(
            f"S'esperaven {EXPECTED_EDITION_COUNT} edicions oficials i se n'han trobat "
            f"{len(editions)}"
        )
    return editions


def build_snapshot(*, verified_at: str, session: requests.Session | None = None) -> dict:
    client = session or requests.Session()
    index_response = client.get(SOURCE_INDEX, timeout=30)
    index_response.raise_for_status()
    editions = []
    for year, source_url in discover_editions(index_response.text):
        response = client.get(source_url, timeout=30)
        response.raise_for_status()
        editions.append(parse_edition_page(year=year, source_url=source_url, html=response.text))
    return {
        "verified_at": verified_at,
        "source_index": SOURCE_INDEX,
        "editions": editions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenera la instantània versionada de resultats del Concurs."
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
