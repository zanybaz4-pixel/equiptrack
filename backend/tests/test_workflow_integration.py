"""Exercise the actual API and PostgreSQL migrations using separate DB roles."""
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta, timezone
from secrets import token_urlsafe
from time import monotonic, sleep
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app import administration, catalog, lending
from app.config import get_settings
from app.db import get_db
from app.main import app
from app.security import COOKIE, hasher, token_hash

pytestmark = pytest.mark.postgres
ORIGIN = "https://equiptrack.test"
MANILA = timezone(timedelta(hours=8))


@pytest.fixture(scope="module")
def engines():
    owner_url = os.environ.get("TEST_API_DATABASE_URL")
    runtime_url = os.environ.get("TEST_API_RUNTIME_URL")
    if not owner_url or not runtime_url:
        pytest.skip("Set both TEST_API database URLs to run the PostgreSQL API workflows.")
    owner, runtime = make_url(owner_url), make_url(runtime_url)
    if (not owner.database or not owner.database.startswith("equiptrack_test_")
            or (owner.host, owner.port, owner.database) != (runtime.host, runtime.port, runtime.database)
            or runtime.username != "equiptrack_app" or owner.username == runtime.username
            or owner.get_backend_name() != "postgresql" or runtime.get_backend_name() != "postgresql"):
        pytest.fail("Use a disposable equiptrack_test_* PostgreSQL DB with separate owner and equiptrack_app URLs.")
    owner_engine = create_engine(owner, hide_parameters=True)
    runtime_engine = create_engine(runtime, pool_pre_ping=True, hide_parameters=True)
    try:
        with owner_engine.connect() as db:
            # Fail early if this is the wrong schema instead of trying to mutate it.
            assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0006_tool_room_directory"
        yield owner_engine, runtime_engine
    finally:
        runtime_engine.dispose()
        owner_engine.dispose()


@pytest.fixture
def clock(monkeypatch):
    class WorkflowClock(datetime):
        instant = datetime(2031, 6, 1, 8, 0, tzinfo=UTC)

        @classmethod
        def now(cls, tz=None):
            return cls.instant.astimezone(tz) if tz else cls.instant.replace(tzinfo=None)

    for module in (lending, catalog, administration):
        monkeypatch.setattr(module, "datetime", WorkflowClock)
    return WorkflowClock


@pytest.fixture(scope="module")
def test_password():
    password = token_urlsafe(24)
    return password, hasher.hash(password)


class Actor:
    def __init__(self, client, credentials, user_id):
        self.client = client
        self.credentials = credentials
        self.id = user_id
        self.token = None
        self.csrf = None

    def login(self):
        response = self.client.post("/api/auth/login", json=self.credentials, headers={"Origin": ORIGIN})
        assert response.status_code == 200, response.json()
        self.token = response.cookies[COOKIE]
        self.csrf = response.json()["csrf_token"]
        return response

    def write(self, method, path, body=None, *, headers=None):
        if self.csrf is None:
            self.login()
        if headers is None:
            headers = {"Origin": ORIGIN, "X-CSRF-Token": self.csrf}
        if body is None:
            return self.client.request(method, path, headers=headers)
        return self.client.request(method, path, json=body, headers=headers)


@pytest.fixture
def workflow(engines, test_password, monkeypatch):
    owner, runtime = engines
    password, password_hash = test_password
    fixture_id = uuid4().hex[:14]

    def db_session():
        with Session(runtime) as db:
            yield db

    monkeypatch.setenv("APP_ORIGIN", ORIGIN)
    get_settings.cache_clear()
    monkeypatch.setitem(app.dependency_overrides, get_db, db_session)

    with owner.begin() as db:
        category_id = db.scalar(text("INSERT INTO equipment_categories(name) VALUES (:name) RETURNING id"),
                                {"name": f"Integration {fixture_id}"})
        item = db.execute(text("""INSERT INTO equipment_items (category_id, asset_code, name, location)
            VALUES (:category_id, :asset_code, :name, 'Synthetic test room') RETURNING id, asset_code"""),
            {"category_id": category_id, "asset_code": f"QA-{fixture_id.upper()}", "name": f"QA item {fixture_id}"}
        ).mappings().one()
        records = {}
        for key, role, kind in (("borrower", "borrower", "student"), ("other", "borrower", "faculty"),
                                ("custodian", "admin", None), ("second", "admin", None)):
            email = f"{key}-{fixture_id}@example.invalid"
            user_id = db.scalar(text("""INSERT INTO users(email,full_name,password_hash,role,borrower_type)
                VALUES(:email,:name,:hash,:role,:kind) RETURNING id"""),
                {"email": email, "name": f"Synthetic {key}", "hash": password_hash, "role": role, "kind": kind})
            records[key] = ({"email": email, "password": password}, user_id)
    try:
        with ExitStack() as stack:
            actors = {
                key: Actor(stack.enter_context(TestClient(app, base_url=ORIGIN, raise_server_exceptions=False)),
                           credentials, user_id)
                for key, (credentials, user_id) in records.items()
            }
            yield owner, item, actors
    finally:
        get_settings.cache_clear()


def create_request(actor, item, start, end, **fields):
    body = {"equipment_id": item["id"], "borrow_at": start.isoformat(), "due_at": end.isoformat(),
            "purpose": "Synthetic integration request"}
    return actor.write("POST", "/api/requests", {**body, **fields})


def recovery_capture(monkeypatch):
    from app import recovery
    messages = []
    monkeypatch.setattr(recovery, "mail_ready", lambda: True)
    monkeypatch.setattr(recovery, "send_password_reset", lambda email, token: messages.append((email, token)))
    return messages


def request_recovery(actor, email=None):
    return actor.client.post("/api/auth/forgot-password", headers={"Origin": ORIGIN},
                             json={"email": email or actor.credentials["email"]})


def test_recovery_requests_are_neutral_and_tokens_are_hashed(workflow, monkeypatch):
    from app.security import token_hash
    owner, _, actors = workflow
    borrower = actors["borrower"]
    messages = recovery_capture(monkeypatch)
    known = request_recovery(borrower, borrower.credentials["email"].upper())
    unknown = request_recovery(borrower, "missing-recovery@example.invalid")
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(messages) == 1
    email, token = messages[0]
    assert email == borrower.credentials["email"] and len(token) == 43
    assert token not in known.text
    with owner.connect() as db:
        stored = db.scalar(text("SELECT token_hash FROM password_reset_tokens WHERE user_id=:id"), {"id": borrower.id})
        assert stored == token_hash(token) and stored != token
    assert request_recovery(borrower).status_code == 202
    assert len(messages) == 1


def test_recovery_changes_password_once_and_revokes_only_its_sessions(workflow, monkeypatch):
    from app.security import verify_password
    owner, _, actors = workflow
    borrower, other = actors["borrower"], actors["other"]
    borrower.login()
    other.login()
    messages = recovery_capture(monkeypatch)
    assert request_recovery(borrower).status_code == 202
    token = messages[0][1]
    body = {"token": token, "password": "Recovery-test-password-42"}
    response = borrower.client.post("/api/auth/reset-password", json=body, headers={"Origin": ORIGIN})
    assert response.status_code == 200, response.text
    assert borrower.client.get("/api/auth/me").status_code == 401
    assert other.client.get("/api/auth/me").status_code == 200
    assert borrower.client.post("/api/auth/login", json=borrower.credentials, headers={"Origin": ORIGIN}).status_code == 401
    assert borrower.client.post("/api/auth/login", json={**borrower.credentials, "password": body["password"]},
                                headers={"Origin": ORIGIN}).status_code == 200
    assert borrower.client.post("/api/auth/reset-password", json=body, headers={"Origin": ORIGIN}).status_code == 400
    with owner.connect() as db:
        assert verify_password(body["password"], db.scalar(text("SELECT password_hash FROM users WHERE id=:id"), {"id": borrower.id}))
        assert db.scalar(text("SELECT count(*) FROM password_reset_tokens WHERE user_id=:id"), {"id": borrower.id}) == 0
        details = db.scalar(text("SELECT details FROM audit_logs WHERE actor_id=:id AND action='auth.password_reset'"), {"id": borrower.id})
        assert details == {}


@pytest.mark.parametrize("inactive", [False, True])
def test_expired_or_deactivated_recovery_link_is_rejected(workflow, monkeypatch, inactive):
    owner, _, actors = workflow
    borrower = actors["borrower"]
    messages = recovery_capture(monkeypatch)
    request_recovery(borrower)
    with owner.begin() as db:
        if inactive:
            db.execute(text("UPDATE users SET is_active=false WHERE id=:id"), {"id": borrower.id})
        else:
            db.execute(text("UPDATE password_reset_tokens SET created_at=now()-interval '2 hours', expires_at=now()-interval '1 hour' WHERE user_id=:id"), {"id": borrower.id})
    response = borrower.client.post("/api/auth/reset-password", headers={"Origin": ORIGIN},
                                    json={"token": messages[0][1], "password": "Recovery-test-password-42"})
    assert response.status_code == 400


def test_recovery_delivery_quota_is_shared_and_expires(engines):
    from app.recovery import delivery_allowed
    _, runtime = engines
    email = f"quota-{uuid4().hex}@example.invalid"
    now = datetime.now(UTC)
    with Session(runtime) as db:
        assert delivery_allowed(db, email, now)
        db.commit()
    for attempt in range(1, 5):
        with Session(runtime) as db:
            assert delivery_allowed(db, email, now + timedelta(seconds=61 * attempt))
            db.commit()
    with Session(runtime) as db:
        assert not delivery_allowed(db, email, now + timedelta(minutes=10))
        db.commit()
    with Session(runtime) as db:
        assert delivery_allowed(db, email, now + timedelta(hours=1, seconds=1))
        db.commit()


def test_concurrent_recovery_link_use_succeeds_only_once(workflow, monkeypatch):
    _, _, actors = workflow
    borrower = actors["borrower"]
    messages = recovery_capture(monkeypatch)
    request_recovery(borrower)
    body = {"token": messages[0][1], "password": "Recovery-race-password-42"}
    def reset():
        return borrower.client.post("/api/auth/reset-password", json=body, headers={"Origin": ORIGIN}).status_code
    with ThreadPoolExecutor(max_workers=2) as workers:
        assert sorted(workers.map(lambda _: reset(), range(2))) == [200, 400]


def approve(actor, request_id):
    return actor.write("PATCH", f"/api/requests/{request_id}/decision", {"decision": "approved"})


def release(actor, request_id):
    return actor.write("POST", f"/api/requests/{request_id}/release", {"condition": "good"})


def decision_id(response, expected):
    assert response.status_code == expected, response.json()
    return response.json()["id"]


def audit_actions(db, request_id):
    return db.scalars(text("""SELECT action FROM audit_logs
        WHERE entity_type='request' AND entity_id=:id ORDER BY id"""), {"id": request_id}).all()


def race_while_equipment_locked(owner, item_id, *operations):
    """Prove both requests reached separate PostgreSQL lock waits before release."""
    with ThreadPoolExecutor(max_workers=len(operations)) as workers:
        with owner.connect() as lock:
            lock.execute(text("SELECT id FROM equipment_items WHERE id=:id FOR UPDATE"), {"id": item_id})
            futures = [workers.submit(operation) for operation in operations]
            try:
                with owner.connect().execution_options(isolation_level="AUTOCOMMIT") as observer:
                    deadline = monotonic() + 6
                    blocked = 0
                    while monotonic() < deadline:
                        blocked = observer.scalar(text("""SELECT count(DISTINCT pid)
                            FROM pg_stat_activity WHERE datname=current_database()
                            AND usename='equiptrack_app' AND wait_event_type='Lock'
                            AND query LIKE '%FROM equipment_items%' AND query LIKE '%FOR UPDATE%'"""))
                        if blocked == len(operations):
                            break
                        if any(future.done() for future in futures):
                            break
                        sleep(0.04)
                    assert blocked == len(operations), f"Expected {len(operations)} separate lock waiters, saw {blocked}."
            finally:
                lock.rollback()
        return [future.result(timeout=8) for future in futures]


def test_concurrent_overlapping_approvals_and_duplicate_release(workflow, clock):
    owner, item, actors = workflow
    first, second = actors["custodian"], actors["second"]
    first.login()
    second.login()
    start = clock.instant + timedelta(hours=1)
    end = start + timedelta(hours=1)
    a = decision_id(create_request(actors["borrower"], item, start, end), 201)
    b = decision_id(create_request(actors["other"], item, start + timedelta(minutes=15), end), 201)
    outcomes = race_while_equipment_locked(owner, item["id"], lambda: approve(first, a), lambda: approve(second, b))
    assert sorted(result.status_code for result in outcomes) == [200, 409]
    winning_request = next(result.json() for result in outcomes if result.status_code == 200)
    winner = winning_request["id"]
    loser = b if winner == a else a
    assert release(first, winner).status_code == 409  # before approved start
    clock.instant = datetime.fromisoformat(winning_request["borrow_at"])
    outcomes = race_while_equipment_locked(owner, item["id"], lambda: release(first, winner), lambda: release(second, winner))
    assert sorted(result.status_code for result in outcomes) == [201, 409]
    with owner.connect() as db:
        assert db.scalar(text("SELECT status FROM borrowing_requests WHERE id=:id"), {"id": loser}) == "pending"
        assert db.scalar(text("SELECT count(*) FROM loan_records WHERE equipment_id=:id AND returned_at IS NULL"),
                         {"id": item["id"]}) == 1
        assert audit_actions(db, winner) == ["request.created", "request.approved", "equipment.released"]
        assert audit_actions(db, loser) == ["request.created"]


def test_adjacent_periods_and_overdue_custody(workflow, clock):
    owner, item, actors = workflow
    borrower, custodian = actors["borrower"], actors["custodian"]
    start = clock.instant + timedelta(hours=1)
    due = start + timedelta(hours=1)
    next_due = due + timedelta(hours=1)
    a = decision_id(create_request(borrower, item, start.astimezone(MANILA), due.astimezone(MANILA)), 201)
    b = decision_id(create_request(borrower, item, due, next_due), 201)
    assert approve(custodian, a).status_code == 200
    assert approve(custodian, b).status_code == 200
    clock.instant = start
    assert release(custodian, a).status_code == 201
    clock.instant = due
    row = borrower.client.get(f"/api/requests/{a}").json()
    assert datetime.fromisoformat(row["due_at"]) == due
    assert not row["is_overdue"]
    assert release(custodian, b).status_code == 409  # adjacent booking cannot override actual custody
    clock.instant = due + timedelta(seconds=1)
    overdue = borrower.client.get("/api/requests", params={"custody": "overdue"}).json()
    assert [row["id"] for row in overdue] == [a]
    assert borrower.client.get("/api/dashboard").json()["overdue"] == 1
    returned = custodian.write("PUT", f"/api/requests/{a}/return", {"condition": "fair"})
    assert returned.status_code == 200 and returned.json()["was_returned_late"]
    assert borrower.client.get("/api/dashboard").json()["overdue"] == 0
    # At the exact due boundary the second request expires for release.
    clock.instant = next_due
    assert release(custodian, b).status_code == 409
    with owner.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM loan_records WHERE request_id=:id"), {"id": b}) == 0


def test_ownership_csrf_rejection_and_pending_cancellation(workflow, clock):
    owner, item, actors = workflow
    borrower, other, custodian = (actors[key] for key in ("borrower", "other", "custodian"))
    start = clock.instant + timedelta(hours=1)
    end = start + timedelta(hours=1)
    request_id = decision_id(create_request(borrower, item, start, end), 201)
    path = f"/api/requests/{request_id}"
    other.login()
    assert other.client.get(path).status_code == 404
    assert other.client.get("/api/requests").json() == []
    assert other.write("DELETE", path).status_code == 404
    assert borrower.write("DELETE", path, headers={"Origin": ORIGIN}).status_code == 403
    assert borrower.write("DELETE", path, headers={"Origin": ORIGIN, "X-CSRF-Token": other.csrf}).status_code == 403
    assert borrower.write("DELETE", path, headers={"Origin": "https://elsewhere.test", "X-CSRF-Token": borrower.csrf}).status_code == 403
    assert borrower.write("PATCH", path + "/decision", {"decision": "approved"}).status_code == 403
    canceled = borrower.write("DELETE", path)
    assert canceled.status_code == 200 and canceled.json()["status"] == "canceled"
    assert borrower.client.get(path).json()["canceled_at"]
    assert borrower.write("DELETE", path).status_code == 409
    rejected = decision_id(create_request(other, item, start, end), 201)
    result = custodian.write("PATCH", f"/api/requests/{rejected}/decision",
                             {"decision": "rejected", "remarks": "Synthetic review note"})
    assert result.status_code == 200 and result.json()["status"] == "rejected"
    assert other.client.get(f"/api/requests/{rejected}").json()["decision_remarks"] == "Synthetic review note"
    with owner.connect() as db:
        assert audit_actions(db, request_id) == ["request.created", "request.canceled"]
        assert audit_actions(db, rejected) == ["request.created", "request.rejected"]


def released_request(actors, item, clock):
    start = clock.instant + timedelta(hours=1)
    request_id = decision_id(create_request(actors["borrower"], item, start, start + timedelta(hours=2)), 201)
    assert approve(actors["custodian"], request_id).status_code == 200
    clock.instant = start
    assert release(actors["custodian"], request_id).status_code == 201
    return request_id


def test_return_is_atomic_and_damaged_equipment_stays_out_of_circulation(workflow, clock, caplog, test_password):
    owner, item, actors = workflow
    request_id = released_request(actors, item, clock)
    borrower, custodian = actors["borrower"], actors["custodian"]
    return_path = f"/api/requests/{request_id}/return"
    marker = f"phase4_fail_return_{request_id}"
    # The identifier is built solely from a server-generated integer in the scratch DB.
    with owner.begin() as db:
        db.execute(text(f"""ALTER TABLE audit_logs ADD CONSTRAINT {marker}
            CHECK (action <> 'equipment.returned' OR entity_id <> {request_id})"""))
    try:
        with caplog.at_level(logging.ERROR, logger="equiptrack"):
            failed = custodian.write("PUT", return_path, {"condition": "damaged", "remarks": "Sensitive-looking synthetic note"})
        assert failed.status_code == 500
        assert failed.json()["error"]["code"] == "internal_error"
        assert failed.headers["X-Request-ID"] == failed.json()["error"]["request_id"]
        for secret in (test_password[0], borrower.token, custodian.token, custodian.csrf, "Sensitive-looking synthetic note", marker):
            assert secret not in failed.text and secret not in caplog.text
    finally:
        with owner.begin() as db:
            db.execute(text(f"ALTER TABLE audit_logs DROP CONSTRAINT {marker}"))
    with owner.connect() as db:
        result = db.execute(text("""SELECT r.status, l.returned_at, l.return_condition, e.condition, e.service_status
            FROM borrowing_requests r JOIN loan_records l ON l.request_id=r.id
            JOIN equipment_items e ON e.id=r.equipment_id WHERE r.id=:id"""), {"id": request_id}).one()
        assert tuple(result) == ("released", None, None, "good", "serviceable")
        assert audit_actions(db, request_id) == ["request.created", "request.approved", "equipment.released"]
    result = custodian.write("PUT", return_path, {"condition": "damaged"})
    assert result.status_code == 200
    assert result.json()["equipment_state"] == "maintenance"
    assert custodian.write("PUT", return_path, {"condition": "good"}).status_code == 409
    assert borrower.client.get(f"/api/equipment/{item['id']}").json()["availability"] == "maintenance"
    start = clock.instant + timedelta(days=1)
    assert create_request(borrower, item, start, start + timedelta(hours=1)).status_code == 409
    with owner.connect() as db:
        assert audit_actions(db, request_id) == [
            "request.created", "request.approved", "equipment.released", "equipment.returned",
        ]


def test_serviceable_return_then_retirement_preserves_history(workflow, clock):
    _, item, actors = workflow
    request_id = released_request(actors, item, clock)
    borrower, custodian = actors["borrower"], actors["custodian"]
    assert custodian.write("PUT", f"/api/requests/{request_id}/return", {"condition": "good"}).status_code == 200
    item_path = f"/api/equipment/{item['id']}"
    current = borrower.client.get(item_path).json()
    assert current["availability"] == "available"
    edit = {key: current[key] for key in ("name", "asset_code", "category_id", "description", "location", "condition")}
    edit["service_status"] = "retired"
    assert custodian.write("PUT", item_path, edit).status_code == 200
    assert borrower.client.get(item_path).json()["availability"] == "retired"
    history = borrower.client.get(f"/api/requests/{request_id}").json()
    assert history["status"] == "returned" and history["loan"]["return_condition"] == "good"
    assert history["asset_code"] == item["asset_code"]


def test_equipment_without_category_is_visible_and_editable(workflow):
    owner, _, actors = workflow
    custodian, borrower = actors["custodian"], actors["borrower"]
    body = {"name": "Synthetic department tool", "asset_code": f"NC-{uuid4().hex[:12]}",
            "location": "RACK-TEST", "condition": "good", "service_status": "serviceable"}
    created = custodian.write("POST", "/api/equipment", body)
    assert created.status_code == 201, created.json()
    item = created.json()
    assert item["category_id"] is None and item["category"] is None
    borrower.login()
    detail = borrower.client.get(f"/api/equipment/{item['id']}")
    assert detail.status_code == 200 and detail.json()["name"] == body["name"]
    listed = borrower.client.get("/api/equipment", params={"q": body["asset_code"]}).json()
    assert [row["id"] for row in listed["items"]] == [item["id"]]
    edited = custodian.write("PUT", f"/api/equipment/{item['id']}", {**body, "location": "RACK-UPDATED"})
    assert edited.status_code == 200 and edited.json()["category_id"] is None
    with owner.connect() as db:
        assert db.scalar(text("SELECT location FROM equipment_items WHERE id=:id"), {"id": item["id"]}) == "RACK-UPDATED"


def test_edit_without_category_preserves_legacy_equipment_category(workflow):
    _, item, actors = workflow
    custodian = actors["custodian"]
    custodian.login()
    path = f"/api/equipment/{item['id']}"
    current = custodian.client.get(path).json()
    body = {key: current[key] for key in ("name", "asset_code", "description", "location", "condition")}
    edited = custodian.write("PUT", path, {**body, "service_status": "serviceable"})
    assert edited.status_code == 200
    assert edited.json()["category_id"] == current["category_id"]
    assert edited.json()["category"] == current["category"]


def test_equipment_can_share_a_storage_rack_and_keep_distinct_identity(workflow):
    _, _, actors = workflow
    custodian, borrower = actors["custodian"], actors["borrower"]
    rack = f"RACK-{uuid4().hex[:10].upper()}"
    body = {"name": "Shared rack tool one", "storage_rack": rack, "location": "MT01.02",
            "condition": "good", "service_status": "serviceable"}
    first = custodian.write("POST", "/api/equipment", body)
    assert first.status_code == 201, first.json()
    second = custodian.write("POST", "/api/equipment", {**body, "name": "Shared rack tool two"})
    assert second.status_code == 201, second.json()
    assert first.json()["asset_code"] != second.json()["asset_code"]
    assert first.json()["storage_rack"] == second.json()["storage_rack"] == rack
    borrower.login()
    found = borrower.client.get("/api/equipment", params={"q": rack}).json()
    assert {row["id"] for row in found["items"]} == {first.json()["id"], second.json()["id"]}
    updated = custodian.write("PUT", f"/api/equipment/{first.json()['id']}", {**body, "storage_rack": "MT08"})
    assert updated.status_code == 200, updated.json()
    assert updated.json()["asset_code"] == first.json()["asset_code"]
    assert updated.json()["storage_rack"] == "MT08"


def test_imported_directory_is_visible_to_borrowers_and_custodians(workflow):
    owner, _, actors = workflow
    with owner.connect() as db:
        imported = db.execute(text("SELECT id,storage_rack,location FROM equipment_items WHERE directory_key IS NOT NULL")).all()
    assert len(imported) == 174
    expected = {row.id: (row.storage_rack, row.location) for row in imported}
    for key in ("borrower", "custodian"):
        actor = actors[key]
        actor.login()
        visible = {}
        offset = 0
        while True:
            response = actor.client.get("/api/equipment", params={"offset": offset, "limit": 100})
            assert response.status_code == 200, response.json()
            page = response.json()
            visible.update({row["id"]: (row["storage_rack"], row["location"]) for row in page["items"]})
            offset += 100
            if offset >= page["total"]: break
        assert all(visible[item_id] == values for item_id, values in expected.items())


def test_location_code_search_finds_directory_items_and_respects_status_filter(workflow):
    _, _, actors = workflow
    borrower = actors["borrower"]
    borrower.login()
    for query in ("MT03.01", "mt03.01"):
        response = borrower.client.get("/api/equipment", params={"q": query, "limit": 100})
        assert response.status_code == 200
        page = response.json()
        assert "Ethyl alcohol" in {row["name"] for row in page["items"]}
        assert all("MT03.01" in row["location"] for row in page["items"])
    available = borrower.client.get("/api/equipment", params={"q": "MT03.01", "availability": "available"}).json()
    assert available["total"] > 0
    maintenance = borrower.client.get("/api/equipment", params={"q": "MT03.01", "availability": "maintenance"}).json()
    assert maintenance["total"] == 0 and maintenance["items"] == []
    by_name = borrower.client.get("/api/equipment", params={"q": "ethyl ALCOHOL"}).json()
    assert [row["name"] for row in by_name["items"]] == ["Ethyl alcohol"]


def test_request_search_finds_equipment_location_with_literal_wildcards(workflow, clock):
    owner, item, actors = workflow
    location = f"Location%_only-{uuid4().hex[:10]}"
    with owner.begin() as db:
        db.execute(text("UPDATE equipment_items SET location=:location WHERE id=:id"), {"location": location, "id": item["id"]})
    borrower = actors["borrower"]
    created = create_request(borrower, item, clock.instant + timedelta(hours=1), clock.instant + timedelta(hours=2))
    assert created.status_code == 201
    response = borrower.client.get("/api/requests", params={"q": location.lower()})
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [created.json()["id"]]


def test_expired_forged_and_logged_out_sessions(workflow):
    owner, _, actors = workflow
    borrower, other = actors["borrower"], actors["other"]
    assert borrower.client.get("/api/equipment").status_code == 401
    response = borrower.login()
    cookie = response.headers["set-cookie"].lower()
    assert all(attribute in cookie for attribute in ("secure", "httponly", "samesite=strict", "path=/"))
    with owner.begin() as db:
        stored = db.scalar(text("SELECT token_hash FROM auth_sessions WHERE user_id=:id"), {"id": borrower.id})
        assert stored == token_hash(borrower.token) and stored != borrower.token
        # Expire relative to the API clock, even when PostgreSQL runs on another host.
        db.execute(text("UPDATE auth_sessions SET expires_at=:expired WHERE user_id=:id"),
                   {"expired": datetime.now(UTC) - timedelta(seconds=1), "id": borrower.id})
    assert borrower.client.get("/api/auth/me").status_code == 401
    forged = other.client.get("/api/auth/me", headers={"Cookie": f"{COOKIE}={token_urlsafe(32)}"})
    assert forged.status_code == 401
    borrower.login()
    prior_token = borrower.token
    result = borrower.write("POST", "/api/auth/logout")
    assert result.status_code == 200 and result.json()["signed_out"]
    replay = other.client.get("/api/auth/me", headers={"Cookie": f"{COOKIE}={prior_token}"})
    assert replay.status_code == 401
    with owner.connect() as db:
        assert not db.scalar(text("SELECT 1 FROM auth_sessions WHERE token_hash=:token"), {"token": token_hash(prior_token)})


def test_deactivation_and_role_change_revoke_all_sessions(workflow):
    owner, _, actors = workflow
    custodian, borrower, other = (actors[key] for key in ("custodian", "borrower", "other"))
    borrower.login()
    borrower.login()  # two valid server sessions for this account
    other.login()
    update = {"full_name": "Synthetic inactive", "role": "borrower", "borrower_type": "student", "is_active": False}
    assert custodian.write("PUT", f"/api/users/{borrower.id}", update).status_code == 200
    assert borrower.client.get("/api/auth/me").status_code == 401
    disabled = borrower.client.post("/api/auth/login", json=borrower.credentials, headers={"Origin": ORIGIN})
    invalid = borrower.client.post("/api/auth/login", json={**borrower.credentials, "email": "missing@example.invalid"}, headers={"Origin": ORIGIN})
    assert disabled.status_code == invalid.status_code == 401
    assert disabled.json()["error"]["message"] == invalid.json()["error"]["message"]
    promote = {"full_name": "Synthetic promoted", "role": "admin", "borrower_type": None, "is_active": True}
    assert custodian.write("PUT", f"/api/users/{other.id}", promote).status_code == 200
    assert other.client.get("/api/users").status_code == 401
    with owner.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM auth_sessions WHERE user_id IN (:a,:b)"),
                         {"a": borrower.id, "b": other.id}) == 0
    other.login()
    assert other.client.get("/api/users").status_code == 200
    assert custodian.write("PUT", f"/api/users/{custodian.id}", update).status_code == 409


def test_malformed_and_timezone_invalid_inputs_do_not_write(workflow, clock):
    owner, item, actors = workflow
    borrower = actors["borrower"]
    borrower.login()
    malformed = borrower.client.post("/api/requests", content="{", headers={
        "Origin": ORIGIN, "X-CSRF-Token": borrower.csrf, "Content-Type": "application/json",
    })
    assert malformed.status_code == 400 and malformed.json()["error"]["code"] == "bad_request"
    start = clock.instant + timedelta(hours=1)
    due = start + timedelta(hours=1)
    invalid = create_request(borrower, item, start, due, borrow_at=start.replace(tzinfo=None).isoformat())
    assert invalid.status_code == 422
    numeric_dates = {"borrow_at": str(int(start.timestamp())), "due_at": str(int(due.timestamp()))}
    assert create_request(borrower, item, start, due, **numeric_dates).status_code == 422
    assert borrower.client.get("/api/equipment", params=numeric_dates).status_code == 422
    assert create_request(borrower, item, due, start).status_code == 422
    assert create_request(borrower, item, clock.instant - timedelta(seconds=1), due).status_code == 422
    with owner.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM borrowing_requests WHERE equipment_id=:id"),
                         {"id": item["id"]}) == 0
