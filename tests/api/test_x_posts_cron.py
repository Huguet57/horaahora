from backend.application.social_posts import SocialPostSyncResult
from backend.config import Settings
from tests.support.application import make_test_client

PRODUCTION = Settings(
    database_url="sqlite://",
    hour_by_hour_source_enabled=False,
    vercel_env="production",
    cron_secret="cron-secret",
)
AUTHORIZED = {"Authorization": "Bearer cron-secret"}


class SyncStub:
    def __init__(self) -> None:
        self.calls = 0

    def run(self) -> SocialPostSyncResult:
        self.calls += 1
        return SocialPostSyncResult(
            status="completed", fetched=3, candidates=2, discovered=2, accepted=1, rejected=1
        )


def test_x_posts_cron_requires_the_production_secret_and_reports_the_run() -> None:
    sync = SyncStub()
    client = make_test_client(settings=PRODUCTION, social_post_sync=sync)

    assert client.get("/internal/cron/x-posts").status_code == 401
    response = client.get("/internal/cron/x-posts", headers=AUTHORIZED)

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "fetched": 3,
        "candidates": 2,
        "discovered": 2,
        "accepted": 1,
        "rejected": 1,
        "failed": 0,
        "published": 0,
        "source_error": "",
    }
    assert sync.calls == 1


def test_x_posts_cron_reports_a_disabled_tracker() -> None:
    client = make_test_client(settings=PRODUCTION)

    response = client.get("/internal/cron/x-posts", headers=AUTHORIZED)

    assert response.json() == {"status": "disabled"}


def test_x_posts_cron_is_not_available_outside_production() -> None:
    client = make_test_client(social_post_sync=SyncStub())

    assert client.get("/internal/cron/x-posts", headers=AUTHORIZED).status_code == 404
