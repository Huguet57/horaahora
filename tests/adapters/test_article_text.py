import httpx
import pytest

from backend.adapters.content.article_text import MAX_ARTICLE_CHARS, PublisherArticleTextSource


def test_extracts_only_article_prose_and_table_results():
    html = """<nav>Una altra colla fa història</nav><div class="td-post-content">
    <p>La colla estrena un nou local.</p><h2>Un espai propi</h2>
    <div class="td-a-rec">Publicitat: rècord històric</div>
    <script>secret()</script><blockquote class="instagram-media">Veieu Instagram</blockquote>
    <p>Ara disposa de més espai per assajar.</p>
    <div>La primera actuació serà dissabte.</div><table><tr><td>Colla</td><td>3de7</td></tr></table>
    <aside>Notícies relacionades</aside></div><footer>Altres fites històriques</footer>"""
    source = PublisherArticleTextSource(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, headers={"content-type": "text/html; charset=utf-8"}, text=html
            )
        )
    )
    text = source.fetch("https://revistacastells.cat/noticia/", timeout=2)
    assert text == (
        "La colla estrena un nou local. Un espai propi "
        "Ara disposa de més espai per assajar. "
        "La primera actuació serà dissabte. Colla 3de7"
    )


@pytest.mark.parametrize(
    "html",
    [
        '<div class="td-post-content"></div><aside>Notícies</aside>',
        "<body>Cal iniciar sessió per llegir</body>",
    ],
)
def test_missing_article_content_returns_empty_text(html):
    source = PublisherArticleTextSource(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, headers={"content-type": "text/html; charset=utf-8"}, text=html
            )
        )
    )
    assert source.fetch("https://revistacastells.cat/noticia/", timeout=2) == ""


@pytest.mark.parametrize(
    "url",
    [
        "https://unknown.example/story/",
        "http://127.0.0.1/",
        "https://revistacastells.cat.evil.test/",
        "https://revistacastells.cat:8443/",
        "https://user:password@revistacastells.cat/",
        "file:///etc/passwd",
    ],
)
def test_unsupported_urls_do_not_make_requests(url):
    def unexpected(_):
        pytest.fail("Unsupported URL was requested")

    assert (
        PublisherArticleTextSource(transport=httpx.MockTransport(unexpected)).fetch(url, timeout=2)
        == ""
    )


def test_redirects_are_validated_before_following():
    calls = []

    def handle(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"Location": "http://127.0.0.1/private"})

    source = PublisherArticleTextSource(transport=httpx.MockTransport(handle))
    assert source.fetch("https://www.elmoncasteller.cat/noticia/", timeout=2) == ""
    assert len(calls) == 1


def test_body_length_is_bounded():
    source = PublisherArticleTextSource(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                text='<div class="td-post-content"><p>'
                + "a" * (MAX_ARTICLE_CHARS + 100)
                + "</p></div>",
            )
        )
    )
    assert len(source.fetch("https://revistacastells.cat/noticia/", timeout=2)) == MAX_ARTICLE_CHARS


def test_http_error_is_not_retried():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(503)

    with pytest.raises(httpx.HTTPStatusError):
        PublisherArticleTextSource(transport=httpx.MockTransport(handle)).fetch(
            "https://revistacastells.cat/noticia/", timeout=2
        )
    assert len(calls) == 1


def test_reads_public_social_caption_without_needing_article_markup():
    html = """<html><meta property="og:description" content="La colla estrena el seu primer 3de7.">
    <body>Log in to Instagram</body></html>"""
    source = PublisherArticleTextSource(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, headers={"content-type": "text/html"}, text=html)
        )
    )
    assert source.fetch("https://www.instagram.com/p/example/", timeout=2) == (
        "La colla estrena el seu primer 3de7."
    )


def test_reads_generic_article_text_including_public_transcripts():
    html = """<nav>Notícies alienes</nav><article><h1>3 rondes</h1>
    <div>TRANSCRIPCIÓ 00:37 La colla supera la seva millor diada.</div>
    <aside>Altres podcasts</aside></article>"""
    source = PublisherArticleTextSource(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, headers={"content-type": "text/html"}, text=html)
        )
    )
    assert source.fetch("https://www.3cat.cat/3cat/programa/audio/123/", timeout=2) == (
        "3 rondes TRANSCRIPCIÓ 00:37 La colla supera la seva millor diada."
    )


def test_empty_publisher_body_does_not_extract_adjacent_news_from_article_wrapper():
    html = """<article><div class="td-post-content"></div>
    <div>Notícia següent: Una fita històrica</div></article>"""
    source = PublisherArticleTextSource(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, headers={"content-type": "text/html"}, text=html)
        )
    )
    assert source.fetch("https://revistacastells.cat/hora-a-hora/nota/", timeout=2) == ""


def test_empty_story_does_not_use_site_boilerplate_as_news_content():
    html = '<meta property="og:description" content="Watch this story on Instagram">'
    source = PublisherArticleTextSource(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, headers={"content-type": "text/html"}, text=html)
        )
    )
    assert source.fetch("https://www.instagram.com/stories/colla/123/", timeout=2) == ""
