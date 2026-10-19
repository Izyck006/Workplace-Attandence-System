# Start here: continuation prompt for Antigravity

Use the following prompt with access to the full working directory:

> Continue the Randaframes Attendance multi-office implementation in `C:\Users\T470\Downloads\CODING\randaframes`. Read `ANTIGRAVITY_HANDOFF.md`, `DEPLOYMENT.md` and `VERIFICATION.md` before changing anything. The Windows installer and central API are built, but the live migration, account provisioning, public deployment and physical scanner acceptance are not complete. Preserve the uncommitted work and the pre-existing scanner edits identified in the handoff.
>
> The owner confirmed that existing staff belong to Engineering Kano. There must be seven isolated office accounts: Engineering Kano, Logistics Kano, Logistics Bauchi, Logistics Lagos, Logistics Onitsha, Logistics PH and Logistics Abuja. The master admin sees all offices grouped by location. Keep MongoDB credentials on the central server; do not restore direct MongoDB access in office apps.
>
> First verify the current source/artifacts and investigate the MongoDB DNS failure without printing secrets. Inspect legacy timestamp semantics, missing/null office IDs and migration recovery before running bootstrap. Obtain the required owner-controlled hosting access; ngrok was discussed for a trial, but no tunnel or hosting service was configured. Follow the prioritized remaining-work and acceptance sections of the handoff. Validate real hardware before claiming scanner reliability. Rebuild the installer and update hashes if desktop code changes. Clearly report what is implemented, deployed, tested and still blocked.

## Files to supply

- The **full current source working tree**, including untracked new implementation files. A checkout of the old commit is insufficient.
- `ANTIGRAVITY_HANDOFF.md`, `DEPLOYMENT.md`, `VERIFICATION.md` and this document.
- `release/RandaframesAttendance-Setup-2.0.0.exe` for installer testing.
- `release/server-package.zip` for server-only deployment; it is not the full source project.
- `release/SHA256SUMS.txt` and optional `release/dashboard-preview.png`.

Do not paste `.env`, database passwords, ngrok tokens, fingerprint captures, private snapshots or generated credential CSV contents into a public handoff. Provide necessary operational secrets separately through the owner's private environment/access mechanism.

The documentation ZIP contains documentation and a preview only. It does not contain the installer, full source tree or secrets.
