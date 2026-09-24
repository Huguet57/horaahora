import logging
import time

from backend.domain.content.models import HourByHourItem
from backend.domain.notifications.models import NotificationIngestionResult
from backend.domain.notifications.ports import NewsInterestClassifier, NotificationRepository

logger = logging.getLogger(__name__)
NOTIFICATION_LOCK_KEY = 2_026_072_201


class NotificationIngestionService:
    """Called with NOTIFICATION_LOCK_KEY held by the cron or CLI entrypoint."""

    def __init__(
        self,
        repository: NotificationRepository,
        classifier: NewsInterestClassifier,
        groups: list[str],
    ):
        self.repository, self.classifier, self.groups = repository, classifier, groups

    def ingest(self, items: list[HourByHourItem], *, deadline: float | None = None):
        deadline = deadline if deadline is not None else time.monotonic() + 45
        ingestion = self.repository.ingest_hour_by_hour(items)
        skipped = self.repository.recover_interrupted_classifications()
        classified = 0
        groups = sorted(set(self.groups + self.repository.observed_groups()))
        for candidate in self.repository.pending_classifications():
            remaining = deadline - time.monotonic()
            if remaining < 0.1:
                break
            if not self.repository.begin_classification(candidate.id):
                continue
            started = time.monotonic()
            try:
                result = self.classifier.classify(
                    candidate.title, candidate.summary, groups, timeout=min(8, remaining)
                )
            except Exception as error:
                self.repository.skip_classification(candidate.id, type(error).__name__)
                skipped += 1
                logger.warning(
                    "news_classification_skipped id=%s reason=%s",
                    candidate.id,
                    type(error).__name__,
                )
                continue
            self.repository.complete_classification(candidate.id, result)
            classified += 1
            logger.info(
                "news_classified id=%s level=%s model=%s criteria=%s latency_ms=%d usage=%s",
                candidate.id,
                result.level.value,
                result.model,
                result.criteria_version,
                (time.monotonic() - started) * 1000,
                result.usage,
            )
        return NotificationIngestionResult(
            ingestion.baseline_created, ingestion.notifications_created, classified, skipped
        )
