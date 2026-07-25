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

    @property
    def destination_url(self) -> str:
        """Return linked content only when the excerpt provides a useful destination."""
        return self.embedded_url


def fetch_entries() -> list[Entry]:
    """Compatibility wrapper around the replaceable editorial-source adapter."""
    source = RevistaCastellsHTMLSource(URL)
    return [
        Entry(
            title=item.title,
            excerpt=item.summary,
            url=item.article_url,
            date=item.published_at.isoformat() if item.published_at else "",
            embedded_url=item.action_url or "",
        )
        for item in source.fetch()
    ]
