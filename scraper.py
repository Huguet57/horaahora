from dataclasses import dataclass

from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource


URL = "https://revistacastells.cat/castells-hora-a-hora/"


@dataclass
class Entry:
    title: str
    excerpt: str
    url: str
    date: str
    embedded_url: str = ""


def fetch_entries() -> list[Entry]:
    """Compatibility wrapper around the replaceable editorial-source adapter."""
    source = RevistaCastellsHTMLSource(URL)
    return [
        Entry(
            title=item.title,
            excerpt=item.summary,
            url=item.article_url,
            date=item.published_at.isoformat() if item.published_at else "",
            embedded_url=item.action_url if item.action_url != item.article_url else "",
        )
        for item in source.fetch()
    ]
