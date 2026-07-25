from tests.support.application import make_test_client


def test_chat_contract_does_not_expose_provider() -> None:
    response = make_test_client().post(
        "/v1/chat",
        json={
            "conversation_id": "3a35386d-f0e4-49cc-86d2-18fac079645c",
            "installation_id": "test-installation",
            "locale": "ca-ES",
            "ruleset": "concurs-2026",
            "messages": [{"role": "user", "content": "5d9f o 4d9fa?"}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["winner_label"] == "Amb 4d9fa"
    assert "provider" not in payload
    assert "model" not in payload
