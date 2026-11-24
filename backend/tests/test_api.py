"""HTTP contract tests with explicit database doubles, not persistence evidence."""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_db
from app.main import app
from app.models import User
from app.security import Principal, require_session

ITEM = {
    "id": 1, "asset_code": "ET-TEST-001", "name": "Synthetic projector",
    "description": "Synthetic test item", "location": "Test cabinet", "category_id": 1,
    "category": "Presentation", "condition": "good", "availability": "available",
    "storage_rack": "ET-TEST-001",
}


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_session] = lambda: Principal(User(id=1, role="borrower"), "test")
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


def test_liveness_does_not_require_database(client, db):
    response = client.get("/api/health/live")
    assert response.status_code == 200
    assert response.json()["phase"] == 2
    db.execute.assert_not_called()
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_readiness_checks_schema(client, db):
    assert client.get("/api/health/ready").status_code == 200
    db.execute.assert_called_once()


@pytest.mark.parametrize("path", ["/api/health/ready", "/api/categories", "/api/equipment", "/api/equipment/1"])
def test_database_failure_is_safe_and_consistent(client, db, path):
    secret = "postgresql://person:do-not-leak@db/database"
    db.execute.side_effect = OperationalError("SELECT", {}, Exception(secret))
    db.scalar.side_effect = OperationalError("SELECT", {}, Exception(secret))
    response = client.get(path)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_unavailable"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    assert secret not in response.text


def test_categories_success(client, db):
    db.execute.return_value.mappings.return_value.all.return_value = [
        {"id": 1, "name": "Presentation", "description": "Synthetic category"}
    ]
    assert client.get("/api/categories").json()[0]["name"] == "Presentation"


def test_equipment_list_success_and_pagination(client, db):
    db.scalar.return_value = 1
    db.execute.return_value.mappings.return_value.all.return_value = [ITEM]
    response = client.get("/api/equipment?limit=1")
    assert response.status_code == 200
    assert response.json() == {"items": [ITEM], "total": 1, "offset": 0, "limit": 1}


def test_empty_catalog_is_success(client, db):
    db.scalar.return_value = 0
    db.execute.return_value.mappings.return_value.all.return_value = []
    response = client.get("/api/equipment?q=nothing")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_equipment_detail_success(client, db):
    db.execute.return_value.mappings.return_value.first.return_value = ITEM
    response = client.get("/api/equipment/1")
    assert response.status_code == 200
    assert response.json() == ITEM


def test_equipment_detail_missing(client, db):
    db.execute.return_value.mappings.return_value.first.return_value = None
    response = client.get("/api/equipment/999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "category_id=0",
                                    "availability=unknown", "q=" + "a" * 121])
def test_invalid_filters_fail_before_querying(client, db, query):
    response = client.get("/api/equipment?" + query)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    db.execute.assert_not_called()


@pytest.mark.parametrize("identifier", ["abc", "0", "-1"])
def test_invalid_equipment_ids(client, db, identifier):
    assert client.get("/api/equipment/" + identifier).status_code == 422
    db.execute.assert_not_called()


def test_search_input_is_bound_as_data(client, db):
    db.scalar.return_value = 0
    db.execute.return_value.mappings.return_value.all.return_value = []
    attack = "'; DROP TABLE users; --"
    assert client.get("/api/equipment", params={"q": attack}).status_code == 200
    statement = db.execute.call_args.args[0]
    compiled = statement.compile()
    assert attack not in str(compiled)
    assert attack in compiled.params.values()


@pytest.mark.parametrize("path", ["/api/equipment", "/api/requests"])
def test_search_rejects_null_characters_before_querying(client, db, path):
    response = client.get(path, params={"q": "tool\x00"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    db.execute.assert_not_called()


def test_unknown_route_uses_error_envelope(client):
    response = client.get("/api/not-a-route")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_wrong_method_uses_error_envelope(client):
    response = client.post("/api/health/live")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"
    assert "GET" in response.headers["allow"]


def test_openapi_documents_implemented_routes_only(client):
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    assert "/api/equipment" in response.json()["paths"]
    assert "post" in response.json()["paths"]["/api/requests"]
    assert "400" in response.json()["paths"]["/api/auth/login"]["post"]["responses"]


def test_unexpected_error_hides_details(client, db):
    db.scalar.side_effect = RuntimeError("private information")
    response = client.get("/api/equipment")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    assert "private information" not in response.text
