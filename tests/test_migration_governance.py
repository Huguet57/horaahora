from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def compose_service(configuration: str, name: str) -> str:
    lines = configuration.splitlines()
    marker = f"  {name}:"
    start = lines.index(marker)
    block: list[str] = []
    for line in lines[start + 1 :]:
        if line and not line.startswith(" "):
            break
        if line.startswith("  ") and not line.startswith("    "):
            break
        block.append(line)
    return "\n".join(block)


def test_compose_runs_migrations_before_api_and_jobs() -> None:
    configuration = read("compose.yaml")
    migrate = compose_service(configuration, "migrate")

    assert 'command: ["alembic", "upgrade", "head"]' in migrate
    assert "db:" in migrate
    assert "condition: service_healthy" in migrate

    for service_name in ("api", "agenda-sync"):
        service = compose_service(configuration, service_name)
        assert "migrate:" in service
        assert "condition: service_completed_successfully" in service


def test_production_deploy_serializes_migrate_stage_smoke_and_promote() -> None:
    workflow = read(".github/workflows/deploy-production.yml")

    assert "workflow_dispatch:" in workflow
    assert "contents: read" in workflow
    assert "group: production" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "environment:" in workflow
    assert "name: production" in workflow
    assert "refs/heads/main" in workflow
    assert "vercel@57.0.0" in workflow
    assert "vercel env run -e production" in workflow
    assert "alembic upgrade head" in workflow
    assert "alembic current" in workflow
    assert "vercel deploy --prod --skip-domain" in workflow
    assert "vercel promote" in workflow
    assert workflow.count("/health/ready") == 2
    assert "alembic downgrade" not in workflow

    migrate = workflow.index("alembic upgrade head")
    deploy = workflow.index("vercel deploy --prod --skip-domain")
    first_smoke = workflow.index("/health/ready")
    promote = workflow.index("vercel promote")
    second_smoke = workflow.rindex("/health/ready")
    assert migrate < deploy < first_smoke < promote < second_smoke


def test_main_auto_deploy_is_disabled_but_previews_remain_enabled() -> None:
    configuration = json.loads(read("vercel.json"))

    assert configuration["git"]["deploymentEnabled"] == {"main": False}


def test_expand_contract_and_recovery_policy_is_documented() -> None:
    policy = read("docs/production-deployments.md").lower()
    readme = read("README.md")

    assert "expand/contract" in policy
    assert "alembic downgrade" in policy
    assert "forward" in policy
    assert "production-deployments.md" in readme
