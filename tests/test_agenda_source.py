from datetime import timedelta
from pathlib import Path

from backend.adapters.content.cccc_agenda import CCCCAgendaFixtureSource, CCCCAgendaHTMLSource


FIXTURE = Path(__file__).parents[1] / "backend" / "data" / "cccc_agenda_fixture.html"


def test_extracts_agenda_without_results_and_preserves_source_order() -> None:
    source = CCCCAgendaHTMLSource()

    events = source.parse(FIXTURE.read_text(encoding="utf-8"), year=2026, month=7)

    assert [event.title for event in events] == [
        "Diada de demostració del migdia",
        "Assaig obert de demostració",
        "Diada de demostració del vespre",
    ]
    assert [event.source_order for event in events] == [0, 1, 2]
    assert events[0].local_date.isoformat() == "2026-07-21"
    assert events[0].time_label == "12:00"
    assert events[0].starts_at is not None
    assert events[0].starts_at.utcoffset() == timedelta(hours=2)
    assert events[0].venue == "Plaça de la Vila"
    assert events[0].municipality == "Valls"
    assert events[0].participating_groups == [
        "Colla de demostració A",
        "Colla de demostració B",
    ]
    assert events[0].notes == "Dada simulada per al desenvolupament local."
    assert "Resultats" not in events[0].notes


def test_preserves_imprecise_time_and_accepts_dot_separator() -> None:
    events = CCCCAgendaHTMLSource().parse(
        FIXTURE.read_text(encoding="utf-8"), year=2026, month=7
    )

    assert events[1].time_label == "Tarda"
    assert events[1].starts_at is None
    assert events[1].notes == ""
    assert events[2].time_label == "18.00"
    assert events[2].starts_at is not None
    assert events[2].starts_at.hour == 18


def test_ids_and_revisions_are_stable_but_content_changes_revision() -> None:
    source = CCCCAgendaHTMLSource()
    html = FIXTURE.read_text(encoding="utf-8")

    first = source.parse(html, year=2026, month=7)
    second = source.parse(html, year=2026, month=7)
    changed = source.parse(
        html.replace("Horari subjecte a canvis.", "Horari confirmat."),
        year=2026,
        month=7,
    )

    assert [event.external_id for event in first] == [event.external_id for event in second]
    assert [event.revision for event in first] == [event.revision for event in second]
    assert changed[2].external_id == first[2].external_id
    assert changed[2].revision != first[2].revision


def test_rejects_unexpected_markup_instead_of_deleting_cached_data() -> None:
    source = CCCCAgendaHTMLSource()

    try:
        source.parse("<html><body></body></html>", year=2026, month=7)
    except ValueError as error:
        assert "agenda" in str(error).lower()
    else:
        raise AssertionError("Expected malformed markup to fail")


def test_prefers_desktop_title_when_markup_contains_an_alternate_mobile_title() -> None:
    html = """
    <div id="agenda"><div class="element">
      <div class="element-header">
        <span class="d-none d-md-block">Festa Major de Terrassa</span>
        <span class="d-md-none">Festa Major</span>
      </div>
      <div class="element-body">
        <div class="divTableCell">21/07/2026<br>20:00<br>Plaça<br><span class="cityname">Terrassa</span></div>
        <div class="divTableCell">- Colla A</div>
      </div>
    </div></div>
    """

    events = CCCCAgendaHTMLSource().parse(html, year=2026, month=7)

    assert events[0].title == "Festa Major de Terrassa"


def test_fixture_data_is_clearly_non_official() -> None:
    events = CCCCAgendaFixtureSource(FIXTURE).fetch_month(2026, 7)

    assert {event.source_id for event in events} == {"cccc-fixture"}
    assert all(event.attribution == "Dades de demostració — no oficials" for event in events)
