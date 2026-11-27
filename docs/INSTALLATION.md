# Installation and deployment

## Ubuntu WSL2 and Docker Engine

The primary brief, R5 pp. 10–11, accepts **Docker Engine inside WSL2** for Windows. Section 6.1 explicitly rejects Docker Desktop (p. 13). Set `APP_ORIGIN` to the exact HTTPS URL used by the browser. Full login uses a Secure cookie and requires HTTPS.

The workspace owner must authorize installation before these steps. From Windows PowerShell, install the Ubuntu 24.04 LTS distribution and confirm it appears with version 2. Complete Ubuntu's first-run user setup if prompted. [Microsoft WSL instructions](https://learn.microsoft.com/en-us/windows/wsl/install)

```powershell
wsl --install --distribution Ubuntu-24.04 --web-download --no-launch
wsl --list --verbose
wsl --distribution Ubuntu-24.04
```

Use Docker's signed Ubuntu apt repository. These commands target Ubuntu 24.04 LTS and assume a fresh WSL2 Ubuntu installation. If Docker Engine is already set up inside that distribution, check its existing configuration and versions before modifying packages. [Docker Engine installation](https://docs.docker.com/engine/install/ubuntu/)

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl mkcert
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker
```

Verify the Engine and Compose plugin using the Unix socket inside Ubuntu. Use an authorized Linux account for Docker operations. If your account requires `sudo`, use it consistently for the Compose commands below.

```bash
uname -r
sudo docker --host unix:///var/run/docker.sock version
sudo docker --host unix:///var/run/docker.sock compose version
mkcert -version
```

Record the Engine, Compose and image digests used for the final evaluation. The Engine and Compose commands run inside Ubuntu.

## Configure the application

From WSL Bash after infrastructure approval/setup:

```bash
cd "/path/to/equiptrack"
test -f .env || cp .env.example .env
```

If you copied the example, set two different long random URL-safe passwords in `.env` and use the same values in their corresponding connection URLs. The owner and app role names are `equiptrack_owner` and `equiptrack_app`. The database name is `equiptrack`. The runtime role has the read and write grants assigned by migration `0002_sessions`.

Database role initialization runs only when the PostgreSQL volume is first created. Editing passwords in `.env` later does not rotate passwords stored in an existing database; perform a reviewed password rotation and update URLs together. Never delete a volume to fix a credential mismatch.

## Trusted development HTTPS

Obtain mkcert from its [official project](https://github.com/FiloSottile/mkcert). After separately approving installation of the local development CA in the relevant host/client trust stores, use `mkcert -install` on the appropriate host. This changes system trust and is deliberately not included in automatic startup or the certificate script.

Then generate files (the script refuses to overwrite existing certificates):

```bash
bash scripts/dev-certs.sh
```

For a WSL command-line check, run `CURL_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem" bash scripts/smoke.sh` after startup. The certificate script also saves the public copy at `infra/certs/equiptrack-rootCA.pem`. Curl uses that CA to validate the chain and hostname.

For a later LAN test, include the actual hostname/LAN IP as extra arguments when first generating the certificate, e.g. `bash scripts/dev-certs.sh equiptrack.local 192.168.1.25`. Those are examples; determine the actual network address. Changing certificate names later requires reviewing/replacing existing files. Do not use the example IP blindly.

Nginx expects `infra/certs/equiptrack.pem` and `infra/certs/equiptrack-key.pem`. Never commit private keys. Each device must trust the **same development root CA certificate**, not just the leaf certificate. Transfer only the public root certificate using a trusted channel, verify its fingerprint, and install with the device owner's permission. Never transfer `rootCA-key.pem`. A CA created/trusted inside WSL is not automatically trusted by Windows or a phone. Firefox/Android/iOS may require separate user trust configuration; record actual device results.

## Start the three tiers

```bash
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 180
docker compose ps -a
docker compose --profile tools run --rm seed
CURL_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem" bash scripts/smoke.sh
```

Migrations run as a one-shot service. Check `docker compose logs migrate` if API startup waits/fails. Owner URLs appear only in owner services; no database credentials are baked into frontend build arguments. Database and API ports stay private. An empty unseeded database is valid; seeding is explicit.

Open `https://localhost:8443`; view the real spec at `/api/openapi.json` and interactive docs at `/api/docs`. Swagger's default JS/CSS are served by a CDN. The JSON spec and React application use local assets.

Stop without deleting data: `docker compose stop`. Recreate containers without deleting the named volume: `docker compose down`, then `up --build -d`. Do not use `down -v`, reset SQL, a destructive downgrade or distribution unregister commands.

## Native development (not the final deployment)

Install project-local dependencies with Python and Node available:

```powershell
Set-Location C:\path\to\equiptrack
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
Set-Location frontend
npm ci
```

Native API startup requires a working PostgreSQL instance. In a PowerShell window, set `DATABASE_URL` to a local **runtime-role** connection URL, then:

```powershell
Set-Location C:\path\to\equiptrack\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For a separately approved native development database, set `MIGRATION_DATABASE_URL` to its owner URL, run `..\.venv\Scripts\alembic.exe upgrade head`, then `..\.venv\Scripts\python.exe -m app.seed` in backend. Do not point native development at a real school database. Without PostgreSQL, liveness still runs and catalog/readiness return safe 503 errors.

In another PowerShell window:

```powershell
Set-Location C:\path\to\equiptrack\frontend
npm run dev
```

Open the URL Vite prints, normally `http://127.0.0.1:5173`. Its `/api` requests proxy to loopback port 8000. This loopback HTTP path is for scaffold development only; it does not satisfy the required HTTPS/container acceptance. No mock fallback data is used.

## Second-device LAN acceptance — Phase 5

Start with the loopback deployment. Choose the actual Windows LAN IPv4 address and include it in the certificate SAN. Use that same HTTPS origin on both devices. Set `APP_ORIGIN=https://ACTUAL_HOST_IP:8443` and recreate the API and gateway after updating the configuration. Under WSL2 NAT, the gateway needs a port binding on the WSL interface and a Windows TCP port proxy listening on the selected Windows LAN address. With mirrored networking, check the WSL interface binding and Hyper-V firewall instead. A phone must be able to reach the selected listener on the same private network. Network changes require the workspace owner's permission. [Microsoft WSL networking](https://learn.microsoft.com/en-us/windows/wsl/networking)

Keep PostgreSQL and FastAPI on their internal Compose networks. Scope any Windows inbound rule to TCP 8443 on the private network, ideally to the second device's IP. Under NAT, recheck the WSL IP after a WSL restart. Record the actual IP and connection result during the test.

### Windows laptop using WSL2 NAT

The certificate prepared on November 16 includes the Windows Ethernet address `192.168.1.20`. Confirm this is still the laptop's address on its Private network before using the commands below. Refresh the certificate with the new address if it changed. Keep the Ubuntu shell open throughout the test.

On the already configured host laptop, double-click `Start-EquipTrack-Demo.cmd` in the project folder. Keep its window open during the demo and press Ctrl+C when finished. It uses the existing Windows port forward. If the Windows or WSL IP address changes, update the port forward with the steps below before using the launcher.

In the Ubuntu shell opened in [Phase 5](PHASE5.md#resume-on-this-laptop), find the current WSL address, then publish the gateway on that address. Replace the two placeholders with the observed IPs.

```bash
ip -4 -brief address show eth0
BIND_ADDRESS=WSL_IPV4 APP_ORIGIN=https://WINDOWS_LAN_IPV4:8443 docker compose up -d --wait --wait-timeout 90 api edge
curl --fail --cacert infra/certs/equiptrack-rootCA.pem --resolve WINDOWS_LAN_IPV4:8443:WSL_IPV4 https://WINDOWS_LAN_IPV4:8443/api/health/ready
```

In Administrator PowerShell, use the same addresses. First check the network profile and confirm port 8443 on the selected address is available.

```powershell
Get-NetConnectionProfile
netsh interface portproxy show v4tov4
$lanAddress = 'WINDOWS_LAN_IPV4'
$wslAddress = 'WSL_IPV4'
netsh interface portproxy add v4tov4 "listenaddress=$lanAddress" listenport=8443 "connectaddress=$wslAddress" connectport=8443
New-NetFirewallRule -Name EquipTrack-WSL2-HTTPS-8443 -DisplayName 'EquipTrack WSL2 HTTPS' -Direction Inbound -Action Allow -Protocol TCP -LocalAddress $lanAddress -LocalPort 8443 -RemoteAddress LocalSubnet -Profile Private
curl.exe -4 --cacert infra/certs/equiptrack-rootCA.pem --ssl-revoke-best-effort "https://${lanAddress}:8443/api/health/ready"
```

For the demo, open the LAN URL on both devices. Use the public CA at `infra/certs/equiptrack-rootCA.pem` to establish browser trust with each device owner. Match the SHA-256 fingerprint in [Phase 5](PHASE5.md#resume-on-this-laptop).

On Android, the public certificate is also available as `infra/certs/EquipTrack-Android-CA.crt`. Transfer it over USB, then find **Install a certificate** in Android Settings and choose **CA certificate**. Open the LAN URL in Chrome over the same private network. [Google's Android certificate instructions](https://support.google.com/device-usage-study-help/answer/15713321?co=GENIE.Platform%3DAndroid&hl=en)

On the second device: connect to the same LAN, install/verify public CA trust with permission, open `https://ACTUAL_HOST_IP:8443`, verify no browser certificate warning, sign in as a synthetic borrower, submit a request; on admin device approve/release/return and verify updated borrower history. Test forbidden admin access, invalid credentials, disabled account, restart persistence and damaged-return availability. Record browser/device, URL, time, screenshots and API/database evidence. Do not disable certificate verification to obtain a passing result.

After the demonstration, remove the test listener in Administrator PowerShell using the same `$lanAddress` value.

```powershell
Remove-NetFirewallRule -Name EquipTrack-WSL2-HTTPS-8443
netsh interface portproxy delete v4tov4 "listenaddress=$lanAddress" listenport=8443
```

In Ubuntu, run `docker compose up -d --wait --wait-timeout 90 api edge` to return to the project's loopback settings.

## Backup and safe restore

```bash
bash scripts/backup.sh
bash scripts/restore.sh backups/ACTUAL_FILE.dump equiptrack_restore_drill1
```

The backup script publishes a PostgreSQL custom archive after a successful dump and preserves database grants. It excludes active session rows. The restore validates the archive table of contents, excludes session rows even in older archives, and restores into a newly named database in a transaction. An existing target fails `createdb`. A failed restore can leave a new empty database for review. Keep the source database active until you verify the copy. Use trusted archives from your own deployment. The destination cluster needs the same owner and runtime roles, and older archives created with `--no-acl` need their runtime grants reviewed before cutover. [PostgreSQL backup and restore](https://www.postgresql.org/docs/17/app-pgrestore.html)

Validate schema migration version, table counts, all unique/exclusion/foreign-key constraints, audit immutability, sample request history and a full workflow on the restored copy before declaring recovery successful. The PostgreSQL instance/role setup and configuration are separate from the data dump; retain the reviewed Compose/migrations and secrets separately. Restrict backup access and approve encryption/retention before any real personal data.
