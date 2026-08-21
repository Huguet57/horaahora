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

    context = repository.retrieve(ContestKnowledgeQuery(source="results", result_scope="winners"))

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


def test_retrieves_the_complete_2026_score_ranking_in_descending_order() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    context = repository.retrieve(
        ContestKnowledgeQuery(
            source="scores",
            score_scope="ranking",
            score_outcome="both",
            ranking_selection="full",
        )
    )

    assert "Rànquing de puntuacions del Concurs de Castells 2026" in context
    assert "Ordre: de més a menys punts descarregat" in context
    assert "Posició | Castell | Punts carregat | Punts descarregat" in context
    assert "1 | 3de10sm | 6205 | 7475" in context
    assert "2 | 4de10sm | 5910 | 7120" in context
    assert "47 | 2de6 | 250 | 300" in context
    assert context.index("1 | 3de10sm") < context.index("2 | 4de10sm")
    assert "Colla Joves Xiquets de Valls" not in context


def test_score_ranking_can_focus_on_loaded_points() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    context = repository.retrieve(
        ContestKnowledgeQuery(
            source="scores",
            score_scope="ranking",
            score_outcome="loaded",
            ranking_selection="full",
        )
    )

    assert "Ordre: de més a menys punts carregat" in context
    assert "Posició | Castell | Punts carregat" in context
    assert "Punts descarregat" not in context
    assert "1 | 3de10sm | 6205" in context


def test_builds_a_typed_top_five_ranking_presentation() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    presentation = repository.score_presentation(
        ContestKnowledgeQuery(
            source="scores",
            score_scope="ranking",
            score_outcome="both",
            ranking_selection="top",
            ranking_limit=5,
        )
    )

    assert presentation is not None
    assert presentation.kind == "score_ranking"
    assert presentation.title == "Rànquing de puntuacions 2026"
    assert presentation.outcome == "both"
    assert presentation.focus_notation is None
    assert [row.position for row in presentation.rows] == [1, 2, 3, 4, 5]
    assert [row.notation for row in presentation.rows] == [
        "3de10sm",
        "4de10sm",
        "2de10fmp",
        "Pde7sf",
        "3de9sf",
    ]


def test_builds_a_score_card_for_a_position_query() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    presentation = repository.score_presentation(
        ContestKnowledgeQuery(
            source="scores",
            score_scope="ranking",
            score_outcome="both",
            ranking_selection="position",
            ranking_notation="Pde7sf",
        )
    )

    assert presentation is not None
    assert presentation.kind == "score_card"
    assert presentation.title == "Pde7sf · 4a posició"
    assert presentation.focus_notation == "Pde7sf"
    assert [(row.position, row.notation) for row in presentation.rows] == [(4, "Pde7sf")]
    assert presentation.rows[0].loaded_points == 5280
    assert presentation.rows[0].unloaded_points == 6360


def test_builds_a_score_card_with_neighbors() -> None:
    repository = SnapshotContestKnowledgeRepository.default()

    presentation = repository.score_presentation(
        ContestKnowledgeQuery(
            source="scores",
            score_scope="ranking",
            score_outcome="both",
            ranking_selection="neighbors",
            ranking_notation="Pde7sf",
        )
    )

    assert presentation is not None
    assert presentation.kind == "score_card"
    assert presentation.focus_notation == "Pde7sf"
    assert [(row.position, row.notation) for row in presentation.rows] == [
        (3, "2de10fmp"),
        (4, "Pde7sf"),
        (5, "3de9sf"),
    ]


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
