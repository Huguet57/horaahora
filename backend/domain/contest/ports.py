from typing import Protocol

from backend.domain.contest.models import ContestKnowledgeQuery, ScorePresentation


class ContestKnowledgeRepository(Protocol):
    def retrieve(self, query: ContestKnowledgeQuery) -> str: ...

    def score_presentation(self, query: ContestKnowledgeQuery) -> ScorePresentation | None: ...
