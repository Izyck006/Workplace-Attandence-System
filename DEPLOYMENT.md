# Randaframes multi-office attendance 2.0

## What is included

The Windows desktop connects to a central HTTPS service. Only the service connects to the MongoDB database configured by `MONGODB_URI` in the existing `.env`. Do not copy `.env` to office PCs.

| Office | Login username | Master report location |
| --- | --- | --- |
| Engineering Kano | engineering-kano | Kano |
| Logistics Kano | logistics-kano | Kano |
| Logistics Bauchi | logistics-bauchi | Bauchi |
| Logistics Lagos | logistics-lagos | Lagos |
| Logistics Onitsha | logistics-onitsha | Onitsha |
| Logistics PH | logistics-ph | PH |
| Logistics Abuja | logistics-abuja | Abuja |

The existing master admin login is preserved. If none exists, provisioning creates `master.admin`. New accounts receive independently generated **10-character temporary passwords with letters, digits and symbols**. Passwords are hashed with Argon2 in MongoDB. First login requires a new password. Five failed attempts lock an account for 15 minutes; admin sessions expire after 12 hours, and scanner-only sessions expire after 24 hours. The master admin can reset an office password; this also revokes its sessions.

Office access is checked on the service for reports, enrollment, employee updates and fingerprint matching. A modified desktop query cannot fetch another office's employees. The master sees all seven offices, with separate location and office filters and a grouped CSV sheet. Times display in WAT (UTC+1); timestamps are stored in UTC. Repeated time-ins and time-outs do not duplicate or overwrite the first recorded time. Deactivation preserves history.

## Current rollout status

The installer and server code are prepared locally. No public server has been deployed. The database DNS lookup failed from this PC during verification, so **live migration and account provisioning have not run**. No scanner was detected during the hardware diagnostic, although the SDK loaded. Physical enrollment, recognition accuracy, unplug/replug and installation on a fresh office PC still need acceptance testing.

## 1. Prepare the existing database once

Stop all old desktop/Android clients during migration. Retire old clients which connect directly to MongoDB; they cannot enforce the new office boundaries. Keep the database URI on the server and restrict database access to that server. If a database password has previously been distributed with old installers, rotate it during cutover.

On a trusted administration PC with Python and the project folder:

```powershell
python -m pip install -r requirements-server.txt
python scripts/check_database.py
python -m src.server.bootstrap --legacy-office engineering-kano
```

The bootstrap command uses the current `.env`, writes a private pre-migration snapshot, creates the seven offices, assigns unassigned existing staff and their attendance to Engineering Kano, and converts supported legacy fingerprints without executing arbitrary pickle code. Unconvertible fingerprints are marked for re-enrollment. Already assigned offices and existing accounts are preserved.

New passwords are written to `private/office-credentials.csv`, never to the installer or console. Deliver each office only its own row privately. The snapshot and credential file contain sensitive information; retain them in restricted storage. Provisioning refuses to overwrite a credential file. To resume a partially completed migration, use a new path with `--credentials private/office-credentials-retry.csv`; existing accounts are skipped. The command is intended for one operator, with old applications stopped.

A full MongoDB backup and restore rehearsal should accompany the deployment. The JSONL snapshot preserves BSON types through MongoDB Extended JSON and records each collection name; it is a migration safeguard, not a replacement for scheduled database backups.

## 2A. Quick trial using ngrok

ngrok exposes a service running on your PC through an HTTPS address. That PC and both processes must remain on and connected.

1. Create an ngrok account and install its agent using the [official instructions](https://ngrok.com/docs/getting-started/).
2. Configure the agent with the authtoken from your ngrok dashboard, privately on the host PC.
3. After successful provisioning, run `start_server.bat`.
4. In a second terminal run `ngrok http 8000`.
5. Enter the HTTPS forwarding address shown by ngrok in every desktop app's **Central server address** field.

All seven offices use the same address, each with its own login. Keep the assigned address stable across restarts. If it changes, update the office clients. Do not expose MongoDB itself through ngrok. ngrok does not fix an unreachable database; the service must first pass `python scripts/check_database.py`.

## 2B. Hosted service on Render

This avoids depending on an office PC for availability. See [Render's Docker guide](https://render.com/docs/docker) and [environment variables](https://render.com/docs/configure-environment-variables).

1. Push only reviewed source code to a private Git repository. Never upload `.env`, `private/`, captures, old `dist/` directories, or scanner binaries. This repository contains old build outputs; use the clean server package or review tracked files before publishing anything.
2. Create a Render **Web Service** using this repository and the Docker runtime (the supplied `render.yaml` can also configure the service).
3. Set private `MONGODB_URI` to the value from `.env`; set `MONGODB_DATABASE` to `attendance_db` unless your existing deployment uses another name. Use an always-on instance for office operations.
4. Allow the host's outbound addresses in your MongoDB network rules. Provision the same database once using step 1 above before handing out logins.
5. Deploy. The Dockerfile listens on `0.0.0.0:8000`; use `/health` for the health check. Render detects the bound port. Enter its HTTPS service URL in every desktop client.

Hosting account creation, plan selection/payment, and deployment access remain with the owner. No hosting purchase or external publication has been made by this change.

## 2C. Small VPS with Docker

Copy the server package to the VPS, place the real `.env` there, and add `ATTENDANCE_DOMAIN=attendance.your-domain.example`. Point that domain to the VPS and allow inbound ports 80/443. Restrict MongoDB network access to the VPS. Run:

```sh
docker compose build
mkdir -p private
docker compose run --rm --user root api python -m src.server.bootstrap --legacy-office engineering-kano
docker compose up -d
```

Caddy provides HTTPS; the API port is not published directly. Do not run bootstrap again if you already provisioned the same database from the admin PC. Store private snapshots off-server, monitor `/health`, and enable your MongoDB provider's backups.

## 3. Install at each office

Run `release/RandaframesAttendance-Setup-2.0.0.exe` on 64-bit Windows 10/11. The setup installs the desktop, bundled x64 scanner runtime, and the vendor USB driver MSI. Driver installation needs Windows administrator rights. Restart if the driver asks, then connect the supported Integrated Biometrics scanner directly to USB.

Open the app, enter the shared HTTPS service address and that office's login, and change the temporary password. Add staff and enroll their fingerprints. Click **Open attendance terminal** for check-ins and check-outs. This replaces the admin session with a scanner-only session. Opening management again requires a fresh login. Log out before handing the PC to someone outside the office.

If the scanner is disconnected, the kiosk retries discovery and also provides **Reconnect scanner**. Runtime discovery checks `IBSCAN_SDK_DIR`, the bundled `scanner_runtime`, then the installed vendor SDK. Use the vendor's supported hardware, USB driver, and x64 runtime. The installer cannot make an unsupported scanner compatible. Vendor runtime/driver distribution must follow your existing vendor agreement.

There is no offline attendance queue in this release. The app confirms attendance only after a successful central response; on connection failure it shows an error and the person must retry. If a response was lost after a successful write, retrying the same action safely returns the existing result. Keep each office online.

## 4. Acceptance checks before client handover

- Install on a fresh Windows PC and verify the driver, three-sample enrollment, matching, time-in, time-out, restart, and USB unplug/replug. Test genuine and unrelated fingers and ambiguous matches against your actual staff population; the existing ORB matcher is not a certified biometric matching engine.
- Confirm Abuja cannot see or enroll Kano staff and Engineering Kano remains separate from Logistics Kano.
- Confirm master filters and CSV export include every office under the correct location and WAT time.
- Verify password reset, forced password change, expired sessions, network loss and retry.
- Confirm migration totals, legacy fingerprint conversion counts and restored backup totals before retiring the old system.
- Sign the installer with the client's code-signing certificate for distribution. No signing certificate was available for this build.

## Build and tests

```powershell
python -m pip install -r requirements-test.txt
python -m pytest -q
python -m compileall -q main.py src
powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
```

The build needs the x64 vendor SDK (`IBSCAN_SDK_DIR` can point at its Bin folder) and Inno Setup. The maintained PyInstaller specification is `packaging/desktop.spec`; it excludes server code and `.env`. The old root-level specifications are obsolete. The old root-level scanner/matcher scripts are manual hardware diagnostics; pytest runs the isolated tests in `tests/` and does not contact the live database.

Architecture references: [FastAPI bearer authentication](https://fastapi.tiangolo.com/tutorial/security/first-steps/), [PyInstaller binary inclusion](https://pyinstaller.org/en/stable/spec-files.html), [Caddy request limits](https://caddyserver.com/docs/caddyfile/directives/request_body).
