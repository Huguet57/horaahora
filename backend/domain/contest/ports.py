from typing import Protocol

from backend.domain.contest.models import ContestKnowledgeQuery


class ContestKnowledgeRepository(Protocol):
    def retrieve(self, query: ContestKnowledgeQuery) -> str: ...
