"""Run against a new empty equiptrack_test_* database, never the application DB.

Tests execute real PostgreSQL DDL/DML within rolled-back transactions. The
separate protocol script checks HTTP authorization and concurrent requests.
"""
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.orm import Session

from app.catalog import list_equipment
from app.lending import list_requests, return_equipment
from app.lending_schemas import ReturnIn
from app.models import User
from app.security import Principal

pytestmark = pytest.mark.postgres


@pytest.fixture
def pg():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set; PostgreSQL integration is unverified")
    if not (make_url(url).database or "").startswith("equiptrack_test_"):
        pytest.fail("Use a disposable equiptrack_test_* database.")
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        tables = connection.scalar(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"))
        if tables:
            pytest.fail("Integration database must have an empty public schema.")
        sql = (Path(__file__).parents[1] / "migrations/versions/0001_initial.sql").read_text(encoding="utf-8")
        connection.exec_driver_sql(sql)
        # Additive metadata used by the current ORM; the original constraints
        # remain under test in this rolled-back schema.
        connection.exec_driver_sql("ALTER TABLE equipment_items ADD COLUMN storage_rack varchar(40), ADD COLUMN directory_key varchar(64)")
        connection.execute(text("""INSERT INTO users (email, full_name, password_hash, role, borrower_type)
            VALUES ('borrower@example.invalid', 'Synthetic Borrower', 'not-a-login-hash', 'borrower', 'student'),
                   ('admin@example.invalid', 'Synthetic Custodian', 'not-a-login-hash', 'admin', NULL);
            INSERT INTO equipment_categories(name) VALUES ('Test');
            INSERT INTO equipment_items(category_id,asset_code,name,location) VALUES (1,'TEST-001','Test item','Test room');"""))
        yield connection
        transaction.rollback()
    engine.dispose()


def request(pg, start="2030-01-01T09:00Z", end="2030-01-01T10:00Z", status="approved"):
    return pg.scalar(text("""INSERT INTO borrowing_requests
        (borrower_id,equipment_id,borrow_at,due_at,purpose,status,decided_by,decided_at)
        VALUES (1,1,:start,:end,'Synthetic activity',:status,2,now()) RETURNING id"""),
        {"start": start, "end": end, "status": status})


def test_overlapping_approval_is_rejected(pg):
    request(pg)
    with pytest.raises(IntegrityError):
        with pg.begin_nested():
            request(pg, "2030-01-01T09:30Z", "2030-01-01T11:00Z")


def test_adjacent_reservations_are_allowed(pg):
    request(pg)
    request(pg, "2030-01-01T10:00Z", "2030-01-01T11:00Z")
    assert pg.scalar(text("SELECT count(*) FROM borrowing_requests")) == 2


def test_invalid_date_order_rejected(pg):
    with pytest.raises(IntegrityError):
        with pg.begin_nested():
            request(pg, "2030-01-01T10:00Z", "2030-01-01T09:00Z")


def test_two_active_loans_are_rejected(pg):
    first = request(pg)
    second = request(pg, "2030-01-02T09:00Z", "2030-01-02T10:00Z")
    insert = text("""INSERT INTO loan_records (request_id,equipment_id,released_by,release_condition)
        VALUES (:request,1,2,'good')""")
    pg.execute(insert, {"request": first})
    with pytest.raises(IntegrityError):
        with pg.begin_nested():
            pg.execute(insert, {"request": second})


def test_damaged_item_cannot_be_serviceable(pg):
    with pytest.raises(IntegrityError):
        with pg.begin_nested():
            pg.execute(text("UPDATE equipment_items SET condition='damaged' WHERE id=1"))
    pg.execute(text("UPDATE equipment_items SET condition='damaged',service_status='maintenance' WHERE id=1"))
    with Session(bind=pg) as db:
        assert list_equipment(db, "", None, None, 0, 12)["items"][0]["availability"] == "maintenance"


def test_audit_rows_are_append_only(pg):
    pg.execute(text("INSERT INTO audit_logs(actor_id,action,entity_type,entity_id) VALUES (2,'approved','request',1)"))
    with pytest.raises(DBAPIError):
        with pg.begin_nested():
            pg.execute(text("DELETE FROM audit_logs"))


def test_overdue_active_loan_still_unavailable(pg):
    request_id = request(pg, "2020-01-01T09:00Z", "2020-01-01T10:00Z", status="released")
    pg.execute(text("""INSERT INTO loan_records(request_id,equipment_id,released_by,released_at,release_condition)
        VALUES (:request,1,2,'2020-01-01T09:00Z','good')"""), {"request": request_id})
    with Session(bind=pg) as db:
        assert list_equipment(db, "", None, None, 0, 12)["items"][0]["availability"] == "on_loan"
        future = datetime.now(UTC) + timedelta(days=1)
        result = list_equipment(db, "", None, "on_loan", 0, 12, future, future + timedelta(hours=1))
        assert result["total"] == 1
        borrower = Principal(db.get(User, 1), "test")
        overdue = list_requests(db, borrower, status=None, custody="overdue", q="", offset=0, limit=12)
        assert len(overdue) == 1 and overdue[0].is_overdue
        assert overdue[0].borrower_name is None
        admin = Principal(db.get(User, 2), "test")
        admin_view = list_requests(db, admin, status=None, custody="overdue", q="", offset=0, limit=12)
        assert admin_view[0].borrower_name == "Synthetic Borrower"
        result = return_equipment(request_id, ReturnIn(condition="good"), db, admin)
        assert result.was_returned_late and not result.is_overdue
        assert list_equipment(db, "", None, None, 0, 12)["items"][0]["availability"] == "available"


def test_return_rolls_back_if_audit_insert_fails(pg):
    request_id = request(pg, "2020-01-01T09:00Z", "2020-01-01T10:00Z", status="released")
    pg.execute(text("""INSERT INTO loan_records(request_id,equipment_id,released_by,released_at,release_condition)
        VALUES (:request,1,2,'2020-01-01T09:00Z','good')"""), {"request": request_id})
    pg.execute(text("ALTER TABLE audit_logs ADD CONSTRAINT reject_test_returns CHECK (action <> 'equipment.returned')"))
    with Session(bind=pg, join_transaction_mode="create_savepoint") as db:
        admin = Principal(db.get(User, 2), "test")
        with pytest.raises(IntegrityError):
            return_equipment(request_id, ReturnIn(condition="damaged"), db, admin)
    assert pg.scalar(text("SELECT status FROM borrowing_requests")) == "released"
    assert pg.scalar(text("SELECT returned_at FROM loan_records")) is None
    assert pg.scalar(text("SELECT service_status FROM equipment_items")) == "serviceable"
    assert pg.scalar(text("SELECT count(*) FROM audit_logs")) == 0
