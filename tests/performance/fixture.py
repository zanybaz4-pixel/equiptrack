"""Seed an isolated load-test database and obtain 50 ordinary borrower sessions."""

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from http.cookies import SimpleCookie
from pathlib import Path
from secrets import token_urlsafe
from urllib.request import Request, urlopen

from sqlalchemy import create_engine, text

from app.security import COOKIE, hasher

ORIGIN = "https://localhost:28443"
USER_COUNT = 50


def seed():
    engine = create_engine(os.environ["MIGRATION_DATABASE_URL"], hide_parameters=True)
    if not engine.url.database.startswith("equiptrack_perf_"):
        raise SystemExit("An isolated performance database is required")
    borrowers = []
    with engine.begin() as db:
        category = db.execute(text("""
            INSERT INTO equipment_categories (name, description)
            VALUES ('Performance test equipment', 'Synthetic R7 fixture')
            RETURNING id
        """)).scalar_one()
        for index in range(1, USER_COUNT + 1):
            email = f"performance-{index:02}@example.invalid"
            password = token_urlsafe(18)
            db.execute(text("""
                INSERT INTO users (email, full_name, password_hash, role, borrower_type)
                VALUES (:email, :name, :password_hash, 'borrower', 'student')
            """), {"email": email, "name": f"Performance borrower {index:02}", "password_hash": hasher.hash(password)})
            item = db.execute(text("""
                INSERT INTO equipment_items (category_id, asset_code, name, location)
                VALUES (:category, :asset, :name, 'Synthetic equipment lab')
                RETURNING id
            """), {
                "category": category,
                "asset": f"PERF-{index:02}",
                "name": f"Performance fixture {index:02}",
            }).scalar_one()
            borrowers.append({"email": email, "password": password, "equipment_id": item})
    return borrowers


def login(borrowers):
    sessions = []
    for borrower in borrowers:
        request = Request(
            "http://api:8000/api/auth/login",
            json.dumps({"email": borrower["email"], "password": borrower["password"]}).encode(),
            {"Content-Type": "application/json", "Origin": ORIGIN},
        )
        with urlopen(request, timeout=10) as response:
            cookie = SimpleCookie()
            cookie.load(response.headers["Set-Cookie"])
            sessions.append({
                "equipment_id": borrower["equipment_id"],
                "cookie_name": COOKIE,
                "cookie_value": cookie[COOKIE].value,
                "csrf_token": json.load(response)["csrf_token"],
            })
    start = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(days=7)
    return {
        "origin": ORIGIN,
        "borrow_at": start.isoformat(),
        "due_at": (start + timedelta(hours=2)).isoformat(),
        "borrowers": sessions,
    }


if __name__ == "__main__":
    if os.environ.get("FIXTURE_ORIGIN") != ORIGIN:
        raise SystemExit("An isolated performance API is required")
    os.umask(0o077)
    Path(sys.argv[1]).write_text(json.dumps(login(seed())), encoding="utf-8")
