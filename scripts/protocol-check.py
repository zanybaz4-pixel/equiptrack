"""Run R2 curl cases against a fresh, student-controlled synthetic deployment."""
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Barrier
from time import sleep
from urllib.parse import urlencode, urlsplit


@dataclass
class Session:
    cookie: str
    csrf: str


class ProtocolChecks:
    def __init__(self):
        self.origin = os.environ.get("PROTOCOL_TEST_ORIGIN", "https://localhost:8443").rstrip("/")
        endpoint = urlsplit(self.origin)
        if endpoint.scheme != "https" or endpoint.hostname not in ("localhost", "127.0.0.1") or endpoint.path:
            raise SystemExit("Use a loopback HTTPS origin for the synthetic protocol tests.")
        self.ca = os.environ.get("PROTOCOL_TEST_CA")
        self.accounts = json.loads(os.environ["PROTOCOL_TEST_ACCOUNTS"])
        self.curl = os.environ.get("PROTOCOL_TEST_CURL", "curl")
        self.record = []

    def request(self, method, path, session=None, body=None, raw=None, csrf=True):
        args = [self.curl, "-q", "--silent", "--show-error", "--max-time", "15",
                "--request", method, "--header", f"Origin: {self.origin}",
                "--dump-header", "-", "--write-out", "\n%{http_code}", f"{self.origin}/api{path}"]
        if self.ca:
            args.extend(["--cacert", self.ca])
        if self.ca and os.environ.get("PROTOCOL_TEST_SCHANNEL") == "1":
            # The temporary development CA does not publish a revocation endpoint.
            # Schannel still verifies the certificate chain and hostname.
            args.append("--ssl-revoke-best-effort")
        headers = []
        if session is not None:
            headers.append(f"Cookie: {session.cookie}")
            if csrf:
                headers.append(f"X-CSRF-Token: {session.csrf}")
        if body is not None:
            raw = json.dumps(body)
        if raw is not None:
            headers.append("Content-Type: application/json")
        # Keep credentials, cookies and request bodies out of process arguments.
        config = "\n".join(f"header = {json.dumps(header)}" for header in headers)
        if raw is not None:
            config += f"\ndata-binary = {json.dumps(raw)}"
        args.extend(["--config", "-"])
        result = subprocess.run(args, input=config, capture_output=True, text=True, encoding="utf-8", check=True)
        header_block, output = result.stdout.replace("\r\n", "\n").split("\n\n", 1)
        content, status = output.rsplit("\n", 1)
        return int(status), json.loads(content), header_block

    def expect(self, name, expected, method, path, **options):
        status, body, headers = self.request(method, path, **options)
        entry = {"case": name, "method": method, "path": path,
                 "expected": expected, "actual": status}
        if expected >= 400:
            detail = body.get("error", {})
            entry["error"] = detail.get("code")
            response_id = next(
                (line.partition(":")[2].strip() for line in headers.splitlines()
                 if line.lower().startswith("x-request-id:")), None,
            )
            assert detail.get("request_id") and detail["request_id"] == response_id, entry
        self.record.append(entry)
        assert status == expected, entry
        return body, headers

    def login(self, role):
        body, headers = self.expect(f"{role} login", 200, "POST", "/auth/login", body=self.accounts[role])
        cookie = next(line.split(": ", 1)[1] for line in headers.splitlines() if line.lower().startswith("set-cookie:"))
        assert all(attribute in cookie.lower() for attribute in ("secure", "httponly", "samesite=strict", "path=/"))
        return Session(cookie.split(";", 1)[0], body["csrf_token"]), body["user"]

    def run(self):
        e = self.expect
        e("liveness", 200, "GET", "/health/live")
        e("liveness wrong method", 405, "POST", "/health/live")
        e("readiness", 200, "GET", "/health/ready")
        e("no session", 401, "GET", "/auth/me")
        e("bad JSON", 400, "POST", "/auth/login", raw="{")
        e("wrong password", 401, "POST", "/auth/login", body={**self.accounts["student"], "password": "incorrect"})
        student, student_user = self.login("student")
        faculty, _ = self.login("faculty")
        admin, _ = self.login("admin")
        e("current session", 200, "GET", "/auth/me", session=student)
        e("no category session", 401, "GET", "/categories")
        categories, _ = e("category list", 200, "GET", "/categories", session=student)
        e("no catalog session", 401, "GET", "/equipment")
        catalog, _ = e("catalog list", 200, "GET", "/equipment", session=student)
        item = next(row for row in catalog["items"] if row["availability"] == "available")
        equipment_id = item["id"]
        e("catalog detail", 200, "GET", f"/equipment/{equipment_id}", session=student)
        e("invalid equipment ID", 422, "GET", "/equipment/0", session=student)
        e("catalog rejects Unix timestamp strings", 422, "GET",
          "/equipment?borrow_at=1969693200&due_at=1969696800", session=student)
        e("profile", 200, "GET", "/profile", session=student)
        e("profile without session", 401, "GET", "/profile")
        e("profile update without CSRF", 403, "PATCH", "/profile", session=student, csrf=False, body={"full_name": "Synthetic Name"})
        e("profile update", 200, "PATCH", "/profile", session=student, body={"full_name": "Synthetic Name"})
        e("dashboard", 200, "GET", "/dashboard", session=student)
        e("dashboard without session", 401, "GET", "/dashboard")

        category_body = {"name": "Protocol test equipment"}
        category, _ = e("create category", 201, "POST", "/categories", session=admin, body=category_body)
        e("borrower cannot create category", 403, "POST", "/categories", session=student, body=category_body)
        equipment_body = {"name": "Synthetic test item", "location": "Test room",
                          "category_id": category["id"], "asset_code": "PROTOCOL-001",
                          "condition": "good", "service_status": "serviceable"}
        created, _ = e("create equipment", 201, "POST", "/equipment", session=admin, body=equipment_body)
        e("duplicate asset code", 409, "POST", "/equipment", session=admin, body=equipment_body)
        equipment_path = f"/equipment/{created['id']}"
        e("update equipment", 200, "PUT", equipment_path, session=admin, body={**equipment_body, "condition": "fair"})
        e("borrower cannot edit equipment", 403, "PUT", equipment_path, session=student, body=equipment_body)
        assert categories
        e("list accounts", 200, "GET", "/users", session=admin)
        e("borrower cannot list accounts", 403, "GET", "/users", session=student)
        new_account = {"email": "protocol-new@example.invalid", "full_name": "Synthetic new",
                       "role": "borrower", "borrower_type": "student", "password": self.accounts["faculty"]["password"]}
        user, _ = e("create account", 201, "POST", "/users", session=admin, body=new_account)
        assert "password" not in user and "password_hash" not in user
        e("duplicate email", 409, "POST", "/users", session=admin, body=new_account)
        update = {"full_name": user["full_name"], "role": "borrower", "borrower_type": "student", "is_active": False}
        e("deactivate account", 200, "PUT", f"/users/{user['id']}", session=admin, body=update)
        e("borrower cannot deactivate accounts", 403, "PUT", f"/users/{user['id']}", session=student, body=update)
        e("inactive login", 401, "POST", "/auth/login", body={key: new_account[key] for key in ("email", "password")})

        start = datetime.now(UTC) + timedelta(seconds=5)
        end = start + timedelta(minutes=15)
        body = {"equipment_id": equipment_id, "borrow_at": start.isoformat(), "due_at": end.isoformat(),
                "purpose": "Synthetic equipment lending protocol check"}
        e("request needs session", 401, "GET", "/requests")
        e("request list", 200, "GET", "/requests", session=student)
        e("reverse date order", 422, "POST", "/requests", session=student, body={**body, "due_at": start.isoformat()})
        e("request rejects Unix timestamp strings", 422, "POST", "/requests", session=student,
          body={**body, "borrow_at": str(int(start.timestamp())), "due_at": str(int(end.timestamp()))})
        first, headers = e("create request", 201, "POST", "/requests", session=student, body=body)
        first_path = f"/requests/{first['id']}"
        assert f"location: /api{first_path}" in headers.lower()
        other, _ = e("second pending request", 201, "POST", "/requests", session=faculty, body=body)
        third, _ = e("create cancelable request", 201, "POST", "/requests", session=student, body=body)
        third_path = f"/requests/{third['id']}"
        e("nonowner cannot cancel", 404, "DELETE", third_path, session=faculty)
        e("owner cancels pending", 200, "DELETE", third_path, session=student)
        canceled, _ = e("canceled request is retained", 200, "GET", third_path, session=student)
        assert canceled["status"] == "canceled"
        e("owner reads request", 200, "GET", first_path, session=student)
        e("nonowner cannot read request", 404, "GET", first_path, session=faculty)
        e("borrower cannot approve", 403, "PATCH", f"{first_path}/decision", session=student, body={"decision": "approved"})
        decision = {"decision": "approved"}
        decisions = self.race("PATCH", [f"{first_path}/decision", f"/requests/{other['id']}/decision"], admin, decision, [200, 409])
        winner = next(result[1] for result in decisions if result[0] == 200)
        loser = other if winner["id"] == first["id"] else first
        winner_path = f"/requests/{winner['id']}"
        e("reject remaining request", 200, "PATCH", f"/requests/{loser['id']}/decision", session=admin, body={"decision": "rejected"})
        period = urlencode({"borrow_at": start.isoformat(), "due_at": end.isoformat()})
        reserved, _ = e("period availability", 200, "GET", f"/equipment/{equipment_id}?{period}", session=student)
        assert reserved["availability"] == "reserved"
        e("cannot request reserved interval", 409, "POST", "/requests", session=student,
          body={**body, "borrow_at": (start + timedelta(minutes=1)).isoformat()})
        sleep(max(0, (start - datetime.now(UTC)).total_seconds()) + 0.1)
        e("borrower cannot release", 403, "POST", f"{winner_path}/release", session=student, body={"condition": "good"})
        self.race("POST", [f"{winner_path}/release"] * 2, admin, {"condition": "good"}, [201, 409])
        active, _ = e("active custody", 200, "GET", "/requests?custody=active", session=admin)
        assert any(row["id"] == winner["id"] for row in active)
        returned, _ = e("damaged return", 200, "PUT", f"{winner_path}/return", session=admin,
                        body={"condition": "damaged", "remarks": "Synthetic damage"})
        assert returned["status"] == "returned" and returned["equipment_state"] == "maintenance"
        e("repeat return rejected", 409, "PUT", f"{winner_path}/return", session=admin, body={"condition": "good"})
        maintained, _ = e("returned equipment marked maintenance", 200, "GET", f"/equipment/{equipment_id}", session=student)
        assert maintained["availability"] == "maintenance"
        logs, _ = e("audit log contains lifecycle", 200, "GET", f"/audit-logs?entity_id={winner['id']}", session=admin)
        assert {"request.approved", "equipment.released", "equipment.returned"} <= {
            entry["action"] for entry in logs if entry["entity_type"] == "request"
        }
        e("borrower cannot view audit logs", 403, "GET", "/audit-logs", session=student)
        assert first["borrower_id"] == student_user["id"]
        e("logout requires CSRF", 403, "POST", "/auth/logout", session=student, csrf=False)
        e("logout", 200, "POST", "/auth/logout", session=student)
        e("logged-out cookie rejected", 401, "GET", "/auth/me", session=student)

    def race(self, method, paths, session, body, expected):
        barrier = Barrier(len(paths))

        def request(path):
            barrier.wait(timeout=10)
            return self.request(method, path, session=session, body=body)

        with ThreadPoolExecutor(max_workers=len(paths)) as pool:
            results = list(pool.map(request, paths))
        statuses = sorted(result[0] for result in results)
        self.record.append({"case": "concurrent requests", "method": method, "paths": paths,
                            "expected": expected, "actual": statuses})
        assert statuses == expected, self.record[-1]
        return results


if __name__ == "__main__":
    checks = ProtocolChecks()
    try:
        checks.run()
    finally:
        print(json.dumps(checks.record, indent=2))
