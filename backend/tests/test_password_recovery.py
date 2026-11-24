"""Recovery contracts without a database or outbound email."""
import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app import recovery, recovery_mail
from app.config import get_settings
from app.db import get_db
from app.main import app

ORIGIN = "https://localhost:8443"


@pytest.fixture
def client(monkeypatch):
    db = MagicMock()
    monkeypatch.setitem(app.dependency_overrides, get_db, lambda: db)
    monkeypatch.setenv("APP_ORIGIN", ORIGIN)
    get_settings.cache_clear()
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, db
    get_settings.cache_clear()


def test_disabled_email_reports_unavailable_without_querying_accounts(client, monkeypatch):
    http, db = client
    monkeypatch.setattr(recovery, "mail_ready", lambda: False)
    response = http.post("/api/auth/forgot-password", headers={"Origin": ORIGIN},
                         json={"email": "borrower@example.invalid"})
    assert response.status_code == 503
    assert "custodian" in response.json()["error"]["message"]
    db.scalar.assert_not_called()


@pytest.mark.parametrize("route,body", [
    ("forgot-password", {"email": "borrower@example.invalid"}),
    ("reset-password", {"token": "a" * 43, "password": "Test-password-123"}),
])
def test_recovery_rejects_cross_origin(client, route, body):
    http, db = client
    assert http.post("/api/auth/" + route, json=body,
                     headers={"Origin": "https://wrong.example.invalid"}).status_code == 403
    db.scalar.assert_not_called()


@pytest.mark.parametrize("token,password", [("short", "Test-password-123"), ("a" * 43, "short"),
                                            ("a" * 44, "Test-password-123"), ("!" * 43, "Test-password-123")])
def test_reset_rejects_malformed_tokens_and_weak_passwords(client, token, password):
    http, db = client
    assert http.post("/api/auth/reset-password", json={"token": token, "password": password},
                     headers={"Origin": ORIGIN}).status_code == 422
    db.scalar.assert_not_called()


def test_unknown_token_cannot_reset_an_account(client):
    http, db = client
    db.scalar.return_value = None
    response = http.post("/api/auth/reset-password", headers={"Origin": ORIGIN},
                         json={"token": "a" * 43, "password": "Test-password-123"})
    assert response.status_code == 400
    db.commit.assert_not_called()


def test_email_payload_uses_trusted_https_origin_and_fragment(monkeypatch):
    settings = MagicMock(app_origin="https://equiptrack.example.invalid", mail_from_email="sender@example.invalid",
                         brevo_api_key=SecretStr("test-api-key"))
    monkeypatch.setattr(recovery_mail, "get_settings", lambda: settings)
    opener = MagicMock()
    opener.open.return_value.__enter__.return_value.status = 201
    monkeypatch.setattr(recovery_mail, "build_opener", lambda *_: opener)
    recovery_mail.send_password_reset("borrower@example.invalid", "a" * 43)
    request = opener.open.call_args.args[0]
    body = json.loads(request.data)
    assert request.full_url == "https://api.brevo.com/v3/smtp/email"
    assert body["to"] == [{"email": "borrower@example.invalid"}]
    assert "https://equiptrack.example.invalid/#/reset-password?token=" in body["textContent"]
    assert "15 minutes" in body["textContent"]
    assert "test-api-key" not in body["textContent"]
    assert opener.open.call_args.kwargs["timeout"] == 8


def test_delivery_failure_never_logs_email_key_or_token(monkeypatch, caplog):
    settings = MagicMock(app_origin=ORIGIN, mail_from_email="sender@example.invalid", brevo_api_key=SecretStr("do-not-log-key"))
    monkeypatch.setattr(recovery_mail, "get_settings", lambda: settings)
    opener = MagicMock()
    opener.open.side_effect = RuntimeError("borrower@example.invalid do-not-log-key secret-token")
    monkeypatch.setattr(recovery_mail, "build_opener", lambda *_: opener)
    recovery_mail.send_password_reset("borrower@example.invalid", "secret-token")
    assert "password_reset_delivery_failed" in caplog.text
    for secret in ("borrower@example.invalid", "do-not-log-key", "secret-token"):
        assert secret not in caplog.text
