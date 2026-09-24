"""Bounded, read-only extraction of public text linked by the news feed."""

import time
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

MAX_ARTICLE_CHARS = 20_000
MAX_HTML_BYTES = 2_000_000
_TEXT_SOURCES = {
    "revistacastells.cat",
    "www.revistacastells.cat",
    "elmoncasteller.cat",
    "www.elmoncasteller.cat",
    "instagram.com",
    "www.instagram.com",
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "www.3cat.cat",
    "diaridigital.urv.cat",
    "www.youtube.com",
    "youtube.com",
    "youtu.be",
}
_HEADERS = {"User-Agent": "HoraAHoraApp/1.0 (+https://github.com/Huguet57/horaahora)"}


class PublisherArticleTextSource:
    def __init__(self, *, transport=None):
        self.transport = transport

    def fetch(self, url: str, *, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        with httpx.Client(transport=self.transport, headers=_HEADERS) as client:
            for _ in range(4):
                # Never fetch arbitrary hosts or follow redirects to unapproved hosts.
                if not _supported(url):
                    return ""
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Article fetch deadline exceeded")
                with client.stream("GET", url, timeout=remaining) as response:
                    if response.is_redirect:
                        url = urljoin(url, response.headers.get("location", ""))
                        continue
                    response.raise_for_status()
                    mime = response.headers.get("content-type", "text/html").split(";")[0]
                    if mime not in {"text/html", "application/xhtml+xml"}:
                        return ""
                    body = bytearray()
                    for chunk in response.iter_bytes(chunk_size=16_384):
                        body.extend(chunk)
                        if len(body) > MAX_HTML_BYTES:
                            raise ValueError("Article HTML exceeds size limit")
                        if time.monotonic() >= deadline:
                            raise TimeoutError("Article fetch deadline exceeded")
                    return extract_article_text(
                        body.decode(response.encoding or "utf-8", errors="replace"), url=url
                    )
        return ""


def _supported(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        return (
            parsed.scheme == "https"
            and parsed.hostname in _TEXT_SOURCES
            and parsed.port in {None, 443}
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def extract_article_text(html: str, *, url: str = "") -> str:
    soup = BeautifulSoup(html, "html.parser")
    containers = soup.select(
        ".td-post-content, .tdb_single_content .tdb-block-inner, .entry-content"
    )
    # If a known publisher explicitly has an empty body, do not fall back to
    # surrounding navigation or titles of adjacent articles in the page wrapper.
    if not containers:
        containers = soup.select('[itemprop="articleBody"], article')[:1]
    for container in containers:
        for noise in container.select(
            "script, style, noscript, iframe, nav, aside, footer, form, figure, "
            ".td-a-rec, .td-a-ad, .td-adspot-title, .adsbygoogle, .instagram-media, "
            ".twitter-tweet, .sharedaddy, .related-posts, .td-post-sharing, .elmon-segueix-box"
        ):
            noise.decompose()
        # Some publisher paragraphs are bare text inside divs, not p elements.
        text = " ".join(container.get_text(" ", strip=True).split())
        if text:
            return text[:MAX_ARTICLE_CHARS]
    parsed = urlsplit(url)
    public_post = (
        parsed.hostname in {"instagram.com", "www.instagram.com"}
        and parsed.path.startswith(("/p/", "/reel/"))
    ) or parsed.hostname in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}
    video = parsed.hostname in {"www.youtube.com", "youtube.com", "youtu.be"}
    if public_post or video:
        # Captions can be publicly available even when the rendered body is empty.
        meta = soup.select_one('meta[property="og:description"]')
        if meta:
            return " ".join(str(meta.get("content", "")).split())[:MAX_ARTICLE_CHARS]
    return ""
