from pathlib import Path

from backend.adapters.content.revista_castells import (
    RevistaCastellsHTMLSource,
    clean_hour_by_hour_display_title,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "revista_hour_by_hour.html"


def test_extracts_items_in_source_order_with_embedded_link() -> None:
    source = RevistaCastellsHTMLSource()

    items = source.parse(FIXTURE.read_text(encoding="utf-8"))

    assert [item.title for item in items] == [
        "Dilluns 20, 12h. Segona notícia",
        "Dilluns 20, 10h. Primera notícia",
    ]
    assert [item.display_title for item in items] == ["Segona notícia", "Primera notícia"]
    assert [item.source_order for item in items] == [0, 1]
    assert items[0].published_at.isoformat() == "2026-07-20T12:00:00+02:00"
    assert items[0].action_url == "https://video.example/directe"
    assert items[1].action_url is None
    assert items[0].attribution == "Revista Castells"


def test_normalizes_relative_article_and_action_urls() -> None:
    source = RevistaCastellsHTMLSource("https://revista.example/castells-hora-a-hora/")
    html = """
    <section class="castells-hora-a-hora">
      <article class="td_module_wrap">
        <h3 class="entry-title"><a href="noticia/">Notícia</a></h3>
        <div class="td-excerpt"><a href="/article-complet/">Entreu aquí</a></div>
      </article>
    </section>
    """

    item = source.parse(html)[0]

    assert item.article_url == "https://revista.example/castells-hora-a-hora/noticia/"
    assert item.action_url == "https://revista.example/article-complet/"


def test_external_ids_are_stable() -> None:
    source = RevistaCastellsHTMLSource()
    html = FIXTURE.read_text(encoding="utf-8")

    first = source.parse(html)
    second = source.parse(html)

    assert [item.external_id for item in first] == [item.external_id for item in second]


def test_display_title_handles_editorial_time_variants_without_changing_plain_titles() -> None:
    examples = {
        "Dilluns 20, 14h. El Concurs treu els números de tall.": "El Concurs treu els números de tall.",
        "Dimarts, 21, 19h. ‘El Pom de Baix’ tracta fer castells.": "‘El Pom de Baix’ tracta fer castells.",
        "Diumenge 19, 20.30h. Els de Sant Vicenç recuperen el 3de7a.": "Els de Sant Vicenç recuperen el 3de7a.",
        "Dissabte 18, 20:30 h - Castells a la plaça.": "Castells a la plaça.",
        "Dilluns 19, 13h.Els Verds retallen distància.": "Els Verds retallen distància.",
        "Els Verds amplien gamma a Sitges.": "Els Verds amplien gamma a Sitges.",
        "Dilluns 20, 14h.": "Dilluns 20, 14h.",
    }

    assert {title: clean_hour_by_hour_display_title(title) for title in examples} == examples
