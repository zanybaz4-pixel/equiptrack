"""Optional Render preview entry point; the WSL Compose deployment is unchanged."""
import os
from pathlib import Path
import signal
import subprocess
import sys
from threading import Event
from urllib.parse import urlsplit

import psycopg
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.security import hasher
from app.seed import main as seed_catalog


def postgres_url(value):
    url = make_url(value)
    if url.drivername not in ("postgres", "postgresql", "postgresql+psycopg"):
        raise ValueError("A PostgreSQL connection is required.")
    if not url.host or not url.database or not url.username or not url.password:
        raise ValueError("The database connection is incomplete.")
    return url.set(drivername="postgresql+psycopg")


def browser_origin(environ):
    origin = environ.get("APP_ORIGIN") or environ.get("RENDER_EXTERNAL_URL", "")
    parsed = urlsplit(origin)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        raise ValueError("Set an exact HTTPS browser origin.")
    return origin.rstrip("/")


def runtime_environment(environ, owner_url):
    password = environ["RENDER_RUNTIME_PASSWORD"]
    if len(password) < 24:
        raise ValueError("The runtime database password must have at least 24 characters.")
    child = dict(environ)
    child["DATABASE_URL"] = owner_url.set(
        username="equiptrack_app", password=password
    ).render_as_string(hide_password=False)
    child["APP_ORIGIN"] = browser_origin(environ)
    child["APP_ENV"] = "production"
    for key in list(child):
        if key == "MIGRATION_DATABASE_URL" or key == "RENDER_RUNTIME_PASSWORD" or key.startswith("DEMO_"):
            child.pop(key)
    return child


def prepare_database(environ, owner_url):
    """Serialize provisioning; never reset existing records or account passwords."""
    connection = owner_url.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(connection, autocommit=True, connect_timeout=10) as owner:
        owner.execute("SELECT pg_advisory_lock(215, 2026)")
        try:
            if not owner.execute("SELECT 1 FROM pg_roles WHERE rolname = 'equiptrack_app'").fetchone():
                owner.execute("CREATE ROLE equiptrack_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT")
            owner.execute(sql.SQL("ALTER ROLE equiptrack_app PASSWORD {}").format(
                sql.Literal(environ["RENDER_RUNTIME_PASSWORD"])))
            owner.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
            migration_env = dict(environ)
            migration_env["MIGRATION_DATABASE_URL"] = owner_url.render_as_string(hide_password=False)
            subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                           env=migration_env, check=True)
            # The seed creates only missing synthetic catalog records.
            os.environ["MIGRATION_DATABASE_URL"] = migration_env["MIGRATION_DATABASE_URL"]
            seed_catalog()
            engine = create_engine(owner_url, hide_parameters=True)
            try:
                with engine.begin() as db:
                    for email, name, role, kind, key in (
                        ("custodian@example.invalid", "Demo Custodian", "admin", None, "DEMO_CUSTODIAN_PASSWORD"),
                        ("student@example.invalid", "Demo Student", "borrower", "student", "DEMO_STUDENT_PASSWORD"),
                        ("faculty@example.invalid", "Demo Faculty", "borrower", "faculty", "DEMO_FACULTY_PASSWORD"),
                    ):
                        password = environ[key]
                        if len(password) < 16:
                            raise ValueError("Use generated demonstration passwords.")
                        db.execute(text("""INSERT INTO users
                            (email, full_name, password_hash, role, borrower_type)
                            VALUES (:email, :name, :password, :role, :kind)
                            ON CONFLICT (email) DO NOTHING"""), dict(
                                email=email, name=name, password=hasher.hash(password), role=role, kind=kind))
            finally:
                engine.dispose()
        finally:
            owner.execute("SELECT pg_advisory_unlock(215, 2026)")


def main():
    environ = dict(os.environ)
    owner_url = postgres_url(environ["MIGRATION_DATABASE_URL"])
    child_env = runtime_environment(environ, owner_url)
    port = environ.get("PORT", "10000")
    if not port.isdecimal() or not 1024 <= int(port) <= 65535:
        raise ValueError("PORT must be an unprivileged TCP port.")
    # Providers can mount a fresh /tmp, hiding directories made during the build.
    for directory in ("client", "proxy", "fastcgi", "uwsgi", "scgi"):
        Path("/tmp/nginx", directory).mkdir(parents=True, exist_ok=True)
    prepare_database(environ, owner_url)
    template = Path("/app/infra/render/nginx.conf.template").read_text(encoding="utf-8")
    config = Path("/tmp/equiptrack-nginx.conf")
    config.write_text(template.replace("${PORT}", port), encoding="utf-8")
    stopped = Event()
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: stopped.set())
    children = []
    result = 0
    try:
        children.append(subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000",
            "--no-server-header", "--no-access-log", "--forwarded-allow-ips=127.0.0.1",
        ], env=child_env))
        children.append(subprocess.Popen(["nginx", "-c", str(config), "-g", "daemon off;"], env=child_env))
        while not stopped.wait(0.5):
            if any(child.poll() is not None for child in children):
                result = 1
                break
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    return result


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as failure:
        # Connection strings and account passwords must never enter deploy logs.
        print(f"Render startup failed ({type(failure).__name__}). Check the service's private configuration.",
              file=sys.stderr)
        sys.exit(1)
