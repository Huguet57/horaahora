import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass


URL = "https://revistacastells.cat/castells-hora-a-hora/"


@dataclass
class Entry:
    title: str
    excerpt: str
    url: str
    date: str


def fetch_entries() -> list[Entry]:
    """Scrape the 'Castells Hora a Hora' page and return entries (newest first)."""
    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    container = soup.select_one(".castells-hora-a-hora")
    if not container:
        raise RuntimeError("No s'ha trobat el contenidor .castells-hora-a-hora")

    entries: list[Entry] = []
    for module in container.select(".td_module_wrap"):
        title_el = module.select_one("h3.entry-title a")
        excerpt_el = module.select_one(".td-excerpt")
        date_el = module.select_one("time.entry-date")

        if not title_el:
            continue

        entries.append(Entry(
            title=title_el.get_text(strip=True),
            excerpt=excerpt_el.get_text(strip=True) if excerpt_el else "",
            url=title_el.get("href", ""),
            date=date_el.get_text(strip=True) if date_el else "",
        ))

    return entries
