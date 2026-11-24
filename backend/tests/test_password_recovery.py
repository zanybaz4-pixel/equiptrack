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
from app.config import Settings

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


def test_gmail_payload_is_signed_without_transmitting_the_shared_secret(monkeypatch):
    from hmac import digest
    settings = Settings(_env_file=None, recovery_mail_provider="gmail", app_origin=ORIGIN,
                        gmail_script_url="https://script.google.com/macros/s/example/exec",
                        gmail_relay_secret=SecretStr("test-private-secret-" * 3))
    monkeypatch.setattr(recovery_mail, "get_settings", lambda: settings)
    assert recovery_mail.mail_ready()
    opener = MagicMock()
    response = opener.open.return_value.__enter__.return_value
    response.status = 200
    response.read.return_value = b'{"ok":true}'
    monkeypatch.setattr(recovery_mail, "build_opener", lambda *_: opener)
    recovery_mail.send_password_reset("borrower@example.invalid", "a" * 43)
    request = opener.open.call_args.args[0]
    body = json.loads(request.data)
    message = "\n".join(str(body[key]) for key in ("issued_at", "request_id", "email", "token"))
    assert body["signature"] == digest(settings.gmail_relay_secret.get_secret_value().encode(), message.encode(), "sha256").hex()
    assert settings.gmail_relay_secret.get_secret_value() not in request.data.decode()
    assert body["token"] == "a" * 43
    assert opener.open.call_args.kwargs["timeout"] == 12


@pytest.mark.parametrize("endpoint", ["http://script.google.com/macros/s/example/exec",
    "https://evil.example.invalid/macros/s/example/exec", "https://script.google.com/macros/s/example/dev",
    "https://script.google.com/macros/s/example/exec?extra=1"])
def test_gmail_rejects_untrusted_relay_endpoints(endpoint, monkeypatch):
    settings = Settings(_env_file=None, recovery_mail_provider="gmail", app_origin=ORIGIN,
                        gmail_script_url=endpoint, gmail_relay_secret=SecretStr("x" * 43))
    monkeypatch.setattr(recovery_mail, "get_settings", lambda: settings)
    assert not recovery_mail.mail_ready()


def test_gmail_response_redirect_drops_signed_payload():
    from urllib.request import Request
    request = Request("https://script.google.com/macros/s/example/exec", data=b'private-signed-body')
    handler = recovery_mail.GoogleResponseRedirect()
    redirected = handler.redirect_request(request, None, 302, "", {}, "https://script.googleusercontent.com/macros/echo?id=example")
    assert redirected.get_method() == "GET" and redirected.data is None
    assert handler.redirect_request(request, None, 302, "", {}, "https://evil.example.invalid/") is None
