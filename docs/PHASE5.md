# Phase 5 deployment and recovery

Verified on November 16, 2026, Asia/Manila, against the MIS 215 Term Project Brief (external course material), R3 and R5.

- Ubuntu 24.04 LTS ran under WSL2. Docker Engine 29.9.3 and Compose 5.7.1 built and started the project using Ubuntu's Unix socket. The migration exited successfully, and PostgreSQL, FastAPI, the React web tier and Nginx were healthy. Only HTTPS was published, on loopback port 8443.
- The mkcert 1.4.4 certificate covers `localhost`, the two loopback IP addresses and the laptop's observed LAN IP, `192.168.1.20`. Curl verified the certificate with the local root CA. The frontend and readiness endpoint returned 200; the catalog returned 401 when signed out. Windows also verified the same certificate and readiness endpoint at `192.168.1.20:8443` after enabling the Private Ethernet rule for the Android test.
- The [64 protocol checks](phase5-protocol-results.json) passed over HTTPS on a separate Compose stack. A redirect through Nginx preserved the HTTPS port.
- The [restore drill](phase5-restore-results.json) restored a synthetic backup into a new PostgreSQL database. Counts, the active loan and damaged return, audit history, constraints, and the restricted application's database access were verified. The restored database had zero sign-in sessions. A repeat restore to the same name was rejected. Stopping PostgreSQL returned 503 for readiness while liveness stayed up. Restarting it preserved source data.
- The saved archive matched its recorded SHA-256 checksum. None of the five generated demonstration and database passwords appeared in the deployed frontend files or captured service logs.

The laptop tests used an explicit CA bundle in curl. The user reported opening EquipTrack on Android at the private-network address. The live database showed active student and faculty demo sessions. The supplied My requests screenshot showed pending faculty request #1 for Classroom projector (ET-PJ-001). PostgreSQL then confirmed that request #1 was approved and contained both the `request.created` and `request.approved` audit events. At the check, the borrowing window had yet to start. Browser certificate status, release, and return on the LAN remain to be verified. Follow the [LAN acceptance instructions](INSTALLATION.md#second-device-lan-acceptance-phase-5).

## Resume on this laptop

For local browser access, double-click `Start-EquipTrack-Local.cmd` in the project folder. Wait for the ready message, open `https://localhost:8443`, and keep the launcher window open while using EquipTrack. This starts the existing containers and keeps the WSL session alive without the old four-hour preview limit. It preserves the database. After restarting Windows, open the launcher again. `Start-EquipTrack-Demo.cmd` is the separate same-network demonstration launcher.

From Windows PowerShell, open the installed Ubuntu distribution and keep its shell open while using the app.

```powershell
wsl --distribution Ubuntu-24.04 --user root --cd /mnt/c/Users/bryan/Desktop/EQUIPTRACK
```

Then run these commands in Ubuntu.

```bash
unset DOCKER_CONTEXT
export DOCKER_HOST=unix:///var/run/docker.sock
docker compose up -d --wait --wait-timeout 90
CURL_CA_BUNDLE=infra/certs/equiptrack-rootCA.pem bash scripts/smoke.sh
```

The existing synthetic sign-in passwords are stored privately inside Ubuntu. View them locally in the Ubuntu shell with `cat /root/.local/state/equiptrack/demo-accounts.txt`. Use the app at `https://localhost:8443` once the Windows browser trusts the project's public development CA. The CA's SHA-256 fingerprint is `4D:92:BE:3A:A3:43:31:B1:48:A7:BB:E3:78:DA:B0:F9:3A:31:09:9D:04:B1:79:5A:44:83:51:38:78:95:C1:48`.

## Image digests

| Image | SHA-256 |
| --- | --- |
| `postgres:17.12-alpine` | `a77aa70e641402a21411b92b721c58d10f23b50ae5fdd2333efd22d166e1e5f7` |
| `nginx:1.28-alpine` | `a8b39bd9cf0f83869a2162827a0caf6137ddf759d50a171451b335cecc87d236` |
| `python:3.13-slim` | `e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90` |
| `node:24-alpine` | `116b800c3754b440ee0aa3ed2f20f5bf3d99a554bfd9adeea09ea8017f6e85f5` |
