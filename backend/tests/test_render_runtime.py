"""Deployment configuration boundaries; never contacts a database."""
import pytest

from app.render_runtime import browser_origin, postgres_url, runtime_environment


def test_render_database_url_uses_installed_driver_and_preserves_tls():
    url = postgres_url("postgres://owner:owner-secret@db.example/test?sslmode=require")
    assert url.drivername == "postgresql+psycopg"
    assert url.query["sslmode"] == "require"


@pytest.mark.parametrize("value", ["sqlite:///local.db", "postgresql://db.example/test"])
def test_incomplete_or_non_postgres_connection_is_rejected(value):
    with pytest.raises(ValueError):
        postgres_url(value)


@pytest.mark.parametrize("origin", ["http://example.com", "https://example.com/path",
                                   "https://example.com/?token=x", "https://user:pass@example.com"])
def test_browser_origin_cannot_silently_accept_an_invalid_origin(origin):
    with pytest.raises(ValueError):
        browser_origin({"APP_ORIGIN": origin})


def test_runtime_does_not_inherit_migration_or_provisioning_credentials():
    environ = {
        "MIGRATION_DATABASE_URL": "postgres://owner:owner-secret@db.example/test",
        "RENDER_RUNTIME_PASSWORD": "a-separate-runtime-secret-12345",
        "DEMO_CUSTODIAN_PASSWORD": "provisioning-only-secret",
        "RENDER_EXTERNAL_URL": "https://equiptrack.onrender.com/",
        "PATH": "/usr/bin",
    }
    child = runtime_environment(environ, postgres_url(environ["MIGRATION_DATABASE_URL"]))
    runtime = postgres_url(child["DATABASE_URL"])
    assert runtime.username == "equiptrack_app"
    assert runtime.password == environ["RENDER_RUNTIME_PASSWORD"]
    assert "owner-secret" not in child["DATABASE_URL"]
    assert not any(key.startswith("DEMO_") for key in child)
    assert "MIGRATION_DATABASE_URL" not in child
    assert "RENDER_RUNTIME_PASSWORD" not in child
    assert child["APP_ORIGIN"] == "https://equiptrack.onrender.com"
    assert child["PATH"] == environ["PATH"]


def test_short_runtime_secret_is_rejected_before_provisioning():
    with pytest.raises(ValueError):
        runtime_environment({"RENDER_RUNTIME_PASSWORD": "short"},
                            postgres_url("postgres://owner:secret@db.example/test"))
