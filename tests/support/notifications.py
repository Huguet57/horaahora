from backend.application.notification_ingestion import NotificationIngestionService
from backend.domain.notifications.interest import InterestClassification, InterestLevel


class RoutineNewsClassifier:
    def classify(self, title, summary, groups, *, timeout):
        return InterestClassification(InterestLevel.LOW, frozenset(), "fake", "test", {}, 1.0)


def ingestion_service(repository):
    return NotificationIngestionService(repository, RoutineNewsClassifier(), [])


def ingest(repository, items):
    return ingestion_service(repository).ingest(items)
