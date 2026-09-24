import logging
import time

from backend.domain.content.models import HourByHourItem
from backend.domain.content.ports import ArticleTextSource
from backend.domain.notifications.models import NotificationIngestionResult
from backend.domain.notifications.ports import NewsInterestClassifier, NotificationRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
NOTIFICATION_LOCK_KEY = 2_026_072_201


class NotificationIngestionService:
    """Called with NOTIFICATION_LOCK_KEY held by the cron or CLI entrypoint."""

    def __init__(
        self,
        repository: NotificationRepository,
        classifier: NewsInterestClassifier,
        groups: list[str],
        *,
        article_source: ArticleTextSource | None = None,
    ):
        self.repository, self.classifier, self.groups = repository, classifier, groups
        self.article_source = article_source

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
            started = time.monotonic()
            content = self._article_content(candidate.url, min(5, remaining - 0.1))
            remaining = deadline - time.monotonic()
            if remaining < 0.1:
                # No Jev attempt has started. Keep the row pending for the next cron.
                break
            if not self.repository.begin_classification(candidate.id):
                continue
            try:
                result = self.classifier.classify(
                    candidate.title,
                    candidate.summary,
                    groups,
                    timeout=min(8, remaining),
                    content=content,
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
                "news_classified id=%s level=%s model=%s criteria=%s latency_ms=%d "
                "content_chars=%d usage=%s",
                candidate.id,
                result.level.value,
                result.model,
                result.criteria_version,
                (time.monotonic() - started) * 1000,
                len(content),
                result.usage,
            )
        return NotificationIngestionResult(
            ingestion.baseline_created, ingestion.notifications_created, classified, skipped
        )

    def _article_content(self, url: str, timeout: float) -> str:
        if self.article_source is None or timeout <= 0:
            return ""
        try:
            return self.article_source.fetch(url, timeout=timeout)
        except Exception as error:
            logger.info("news_article_fallback reason=%s", type(error).__name__)
            return ""
