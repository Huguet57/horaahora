from backend.adapters.contest.snapshot import SnapshotContestKnowledgeRepository
from backend.domain.contest.models import ContestKnowledgeQuery


def test_retrieves_only_the_requested_historical_edition() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    context = repository.retrieve(
        ContestKnowledgeQuery(
            source="results",
            years=[1998],
            result_scope="classification",
        )
    )

    assert "Concurs 1998" in context
    assert "Colla Joves Xiquets de Valls" in context
    assert "16.337" in context
    assert "Concurs 2024" not in context
    assert "9465" not in context


def test_filters_results_by_year_and_group() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    context = repository.retrieve(
        ContestKnowledgeQuery(
            source="results",
            years=[2024],
            groups=["Castellers de Vilafranca"],
            result_scope="classification",
        )
    )

    assert "C. de Vilafranca" in context
    assert "9465 punts" in context
    assert "C. Vella dels X. de Valls" not in context


def test_group_filter_matches_full_names_against_official_abbreviations() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    context = repository.retrieve(
        ContestKnowledgeQuery(
            source="results",
            years=[2024],
            groups=["Colla Joves Xiquets de Valls"],
            result_scope="classification",
        )
    )

    assert "C. Joves X. de Valls" in context
    assert "6505 punts" in context
    assert "C. Jove X. de Tarragona" not in context


def test_retrieves_a_compact_winners_view_across_all_editions() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    context = repository.retrieve(
        ContestKnowledgeQuery(source="results", result_scope="winners")
    )

    assert "Guanyadors de les edicions celebrades" in context
    assert "2024 | 1 | C. de Vilafranca" in context
    assert "1932 | 1 | Colla Vella dels Xiquets de Valls" in context
    assert "Ronda 1" not in context


def test_retrieves_rules_without_loading_historical_results() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    context = repository.retrieve(ContestKnowledgeQuery(source="rules"))

    assert "canvis_confirmats_2026" in context
    assert "normativa_completa_2024" in context
    assert "protocol_placa_2024" in context
    assert context.index("canvis_confirmats_2026") < context.index("normativa_completa_2024")
    assert "Colla Joves Xiquets de Valls" not in context


def test_unknown_result_filter_returns_an_explicit_empty_context() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    context = repository.retrieve(
        ContestKnowledgeQuery(
            source="results",
            years=[1900],
            groups=["Colla Inexistent"],
            result_scope="classification",
        )
    )

    assert "No hi ha cap dada coincident" in context
    assert "1900" in context
    assert "Colla Inexistent" in context
    assert "No completis aquesta absència" in context
