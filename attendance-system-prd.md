# Workplace Attendance System: Product Requirements Document

Version 1.1 (draft for review; decisions updated 2026-10-09)
Stack: Python, PySide6 desktop app, MongoDB with PyMongo, Kojack USB fingerprint scanner

---

## 1. Executive Summary

### 1.1 What this is
A desktop application that runs on one computer in the office. Staff put a finger on a USB fingerprint scanner to clock in and clock out. The system identifies who they are, records the time, validates the scan against a set of rules, and stores everything in a local database. The Main Admin manages employees, fingerprints, leave, holidays and corrections. Line managers log in to see the attendance of the people who report to them. At the end of each month the system produces analytics and exportable reports that reviewers use to judge punctuality and attendance themselves.

### 1.2 The problem
Paper registers and manual sign-in sheets are easy to fake (one person signing for another), easy to lose, slow to total up, and hard to audit. Fingerprints tie each record to a real person, and a database makes the monthly summary automatic.

### 1.3 A note on "training a model"
This system does **not** train or retrain any machine-learning model. A fingerprint scanner turns each finger into a template, which is a compact set of ridge features. Adding a new employee means capturing and storing their template. Matching compares a fresh scan against stored templates using the scanner vendor's matching engine. Nothing needs retraining when staff join or leave, which is why this approach is lighter and more accurate than building our own model. See section 7.4 for the options that were considered.

### 1.4 Decisions confirmed during discovery

| Topic | Decision |
|---|---|
| Language / platform | Python |
| Primary verification | Fingerprint, Kojack USB scanner plugged into the office computer |
| Hosting | Local, on one office computer, no internet needed |
| Scale | Under 50 staff, single site |
| Roles | Main Admin, Line Manager, Staff |
| Access | Desktop app on the office PC only |
| Staff access | Scan only, staff have no login |
| Clock logic | First scan of the day is clock-in, next scan is clock-out |
| Schedule | One fixed schedule for everyone |
| Official hours | 09:00 to 17:00; actual attendance may extend beyond 17:00 |
| Lateness | The system does not judge it. It records times and provides analytics; reviewers decide |
| Corrections | Only the Main Admin can edit attendance records |
| Absence rule | Main Admin records leave and public holidays. Any other working day with no scan is absent |
| Database | MongoDB, confirmed; PyMongo for database access |
| Desktop toolkit | PySide6 (recommended, see 7.3) |

---

## 2. Goals & Success Metrics

### 2.1 Goals
1. **Reliable capture.** Every clock-in and clock-out is recorded, even if the app crashes or the power drops right after a scan.
2. **Trustworthy identity.** A record can only be created by the real person's fingerprint, and nobody can silently change it afterwards.
3. **Automatic validation.** Duplicate scans, unknown fingerprints, missing clock-outs and absent days are handled by rules, not by someone checking a sheet.
4. **Useful monthly insight.** Admin and line managers get clear monthly analytics without building spreadsheets by hand.
5. **Simple to run.** One office PC, one installer, automatic backups, minimal upkeep.

### 2.2 Success metrics (proposed targets, to be confirmed in UAT)

| Metric | Target |
|---|---|
| Time from finger placement to on-screen result | 2 seconds or less (95th percentile) |
| Scans accepted on first attempt for enrolled staff | 97% or more |
| False accept rate (wrong person identified) | At or below the scanner vendor's rated figure, and no confirmed wrong-person records in pilot |
| Scans recorded in the scan log | 100% (accepted and rejected) |
| Attendance records matching a manual spot-check during pilot | 99% or more |
| Time to enroll a new employee (details + fingerprints) | Under 3 minutes |
| Monthly report generation time | Under 10 seconds for the full company |
| Automatic backups completed | 100% of scheduled runs, with a restore test passed before go-live |
| Records needing admin correction | Under 5% of working days (tracks scanner reliability and staff habits) |

---

## 3. Scope

### 3.1 In scope
- Employee and department management
- Fingerprint enrollment and deactivation
- Clock-in / clock-out kiosk screen with validation and on-screen feedback
- Daily attendance record generation, including automatic absent marking
- Leave and public holiday calendar (recorded by the Main Admin)
- Admin-only record corrections and manual entries, with reasons
- Line manager view of their own team (read-only)
- Monthly analytics, PDF and Excel/CSV exports
- Audit log of sensitive actions
- Automatic local backups and restore
- Windows installer for the office PC

### 3.2 Out of scope (version 1)
- Staff logins, staff self-service, leave requests from staff
- Mobile app, web access, remote or multi-site use
- Multiple clock-in stations or networked terminals
- Face recognition, card, QR or PIN clock-in
- Automatic lateness flags, penalties, overtime rules or payroll calculation
- Shift patterns, rotating schedules, per-employee schedules
- Email or SMS notifications
- Integration with HR or payroll software
- Employee photos on the kiosk screen
- Tamper-proof hash chaining of audit documents (planned for a later version)

---

## 4. Roles & Permissions

### 4.1 Roles
- **Main Admin.** Oversees the whole system. Sets up employees, departments, fingerprints, schedule, leave, holidays, settings and backups. The only role that can edit attendance records.
- **Line Manager.** An employee who also has a login. Can see attendance and analytics for the staff who report to them, and their own record. Cannot edit anything.
- **Staff.** Has a department and one line manager. Interacts with the system only by scanning a finger. No login.

Line managers are also employees, so they clock in with their fingerprint like everyone else.

### 4.2 Permission matrix

| Capability | Main Admin | Line Manager | Staff |
|---|---|---|---|
| Clock in / out by fingerprint | Yes (if enrolled) | Yes | Yes |
| Log in to the management console | Yes | Yes | No |
| Create / edit / deactivate employees | Yes | No | No |
| Manage departments | Yes | No | No |
| Assign line manager to staff | Yes | No | No |
| Enroll / deactivate fingerprints | Yes | No | No |
| Create line manager logins, reset passwords | Yes | No | No |
| View all attendance records | Yes | Own team and self | No |
| Edit records, add manual entries | Yes | No | No |
| Record leave and public holidays | Yes | No | No |
| View analytics | Company, department, team | Own team and self | No |
| Export reports | All | Own team only | No |
| View audit log | Yes | No | No |
| Change settings, run backup / restore | Yes | No | No |

### 4.3 Rules
- Permissions are enforced in the application service layer, not only by hiding buttons.
- Sensitive admin actions (enroll, edit record, restore backup, reset password) ask the Main Admin to re-enter their password.
- A line manager can only query employees whose `line_manager_id` is their own.

---

## 5. Functional Requirements

Priority: **M** = must have, **S** = should have.

### FR-1 Authentication and Sessions (M)
Applies to Main Admin and Line Managers.

**Business rules**
- First launch runs a setup wizard that creates the Main Admin account and shows a one-time recovery code, to be printed and stored safely.
- Login is username and password. Passwords are at least 10 characters and stored hashed (Argon2).
- 5 failed attempts lock the account for 15 minutes. Failed attempts are logged.
- The console logs out automatically after 10 minutes of inactivity and returns to the kiosk screen, because the PC is shared with the scanner.
- New and reset passwords are temporary; the user must change them at first login.

**Acceptance criteria**
- Given a locked account, when the correct password is entered during the lock, then login is refused and the lock timer is shown.
- Given 10 minutes of no input, when the timeout passes, then the session ends and the kiosk screen appears.
- Given the Main Admin forgot the password, when the recovery code is used, then a new password can be set and the event is audited.

### FR-2 Employees and Departments (M)
**Business rules**
- Employee fields: employee number (auto-generated, e.g. EMP-0001, editable before first scan), full name, department, line manager, phone (optional), status (active or inactive).
- Every active staff member must have a department and a line manager. Line managers and the Main Admin may have no manager.
- A line manager must be an employee with a Line Manager login.
- Employees are never hard-deleted. Deactivating one removes their fingerprints from matching but keeps all history.
- A department cannot be deactivated while it has active employees.
- Changing an employee's department or manager affects future records only. Each attendance record stores a snapshot of department and manager at the time.

**Acceptance criteria**
- Given a new staff member with no line manager selected, when the admin saves, then validation blocks it with a clear message.
- Given a deactivated employee, when they scan, then the kiosk shows "Not recognised" and the event is logged as rejected.
- Given an employee moved to another manager, when last month's report is run, then last month's records still show the old manager.

### FR-3 Fingerprint Enrollment (M)
**Business rules**
- Enrollment is done by the Main Admin from the employee profile, on the office PC.
- At least two fingers are enrolled per person (a main finger and a backup), with several captures each, to reduce failed scans from dirty or injured fingers.
- A capture below the quality threshold is rejected and must be repeated.
- Before saving, the new template is checked against all stored templates. If it matches another employee, enrollment is blocked and the admin is told who it clashes with.
- Only templates are stored, never fingerprint images. Templates are encrypted at rest.
- Attendance scanning is paused while enrollment is running, and a banner says so. It resumes automatically afterwards.
- No retraining step exists. After saving, the template is available for matching immediately.
- Admin can deactivate a finger or re-enroll an employee. Both actions are audited.

**Acceptance criteria**
- Given a good capture of two fingers, when the admin saves, then the employee can clock in within seconds without restarting the app.
- Given a finger already enrolled under another employee, when the admin tries to enroll it, then the system refuses and names the existing employee.
- Given the scanner is unplugged during enrollment, when a capture is attempted, then a clear device error is shown and nothing partial is saved.

### FR-4 Clock-in / Clock-out Kiosk (M)
The kiosk screen is the app's home screen and is always listening for scans.

**Business rules**
- The first accepted scan of a working day is clock-in. The next accepted scan that day is clock-out.
- Official hours are 09:00 to 17:00, used as reporting reference times. Scanning remains available after 17:00; there is no automatic clock-out or cap on recorded hours. A later clock-out on the same calendar day records the actual departure time. Overnight shifts remain outside version 1 scope.
- **Identification:** the scan is matched against all active templates (one-to-many). No match means rejected.
- **Duplicate guard:** a scan by the same person within 60 seconds of their last accepted scan is ignored with an "Already recorded" message, so a double tap cannot become an instant clock-out.
- **Day complete:** after clock-in and clock-out, any further scan that day is rejected with "You have already clocked out today". (See open question Q2.)
- **Write first, show second:** the scan event is saved to the database before the success message is displayed.
- The timestamp comes from the PC clock. If the clock is found to have jumped backwards past the last stored event, scanning is blocked and the screen shows a clock error until the admin resolves it.
- Feedback: large colour-coded message with name, department and time (green for clock-in, blue for clock-out, red for rejection), plus a short sound.
- The kiosk keeps working when the console is open. Scans still record and a toast message appears.
- Every scan, accepted or rejected, goes into `scan_events` and can never be edited or deleted.

**Acceptance criteria**
- Given an enrolled employee's first scan of the day, when it matches, then a clock-in is stored and the screen shows "Clocked IN" with the time within 2 seconds.
- Given an unenrolled finger, when scanned, then a red "Not recognised" message shows and a rejected event is logged.
- Given the PC loses power right after a green confirmation, when it restarts, then that scan is present in the database.
- Given a scan 20 seconds after the same person's clock-in, then no clock-out is created.
- Given an employee clocks in at 09:00 and clocks out at 18:30 on the same day, then the record stores 18:30 and 9 hours 30 minutes worked, without truncating at 17:00.

### FR-5 Attendance Records and Validation (M)
**Business rules**
- One record per employee per work date, built from accepted scans.
- Status values: `present` (in and out), `incomplete` (in, no out), `absent`, `on_leave`, `system_down`.
- Day type: `working`, `off_day` (e.g. weekend), `holiday`.
- Hours worked = clock-out minus clock-in. For `incomplete` records, hours are blank.
- A **day-close job** runs at a configurable time (default 23:59). For every active employee with no scan on a working day that is not a holiday or leave day, it creates an `absent` record.
- A day that has an `incomplete` record stays incomplete until the admin fixes it. It is never auto-completed.
- Scans on off days or holidays are accepted and recorded as `present` with the matching day type.
- **Downtime protection:** the app writes a heartbeat every minute. If the PC or app was off for a working day (no heartbeats in working hours), the job marks that day `system_down` for everyone instead of absent, and the admin is prompted to resolve it.
- On startup the app catches up on any day-close jobs it missed.

**Acceptance criteria**
- Given a working day with no scan and no leave, when day-close runs, then an `absent` record exists.
- Given the PC was off all day, when the app next starts, then that day shows `system_down` for all staff and not absent.
- Given an employee scanned in but never out, then the day shows `incomplete` in all views and reports.

### FR-6 Corrections and Manual Entries (M)
**Business rules**
- Only the Main Admin can change a record: edit times, change status, add a manual record for a missed day, or void an erroneous one.
- A reason code (scanner fault, forgot to scan, approved by management, data entry error, other) and a free-text note are required.
- The original values are preserved in `attendance_corrections` and the record is labelled `source = manual` or shows an "edited" marker.
- The admin must re-enter their password to save a correction.
- Raw `scan_events` are never changed by a correction.
- A correction screen lists all `incomplete`, `system_down` and recent `absent` days in one queue so they can be cleared quickly.

**Acceptance criteria**
- Given an incomplete day, when the admin sets a clock-out time with a reason, then the record becomes `present`, shows as edited, and an audit entry stores old and new values.
- Given a line manager session, when they open a record, then no edit controls appear and a direct service call is refused.

### FR-7 Leave and Holiday Calendar (M)
**Business rules**
- The Main Admin records public holidays (date and name) and leave (employee, start date, end date, type, note). Leave types: annual, sick, maternity or paternity, compassionate, unpaid, other.
- Leave and holidays can be added for past dates. Doing so updates any `absent` records in that range and logs the change.
- The working week (provisionally Monday to Friday) is set in settings and applies to everyone. Confirmed official hours are 09:00 to 17:00; these reference times do not restrict actual scan times.
- Leave over a date that has a clock-in keeps the scan data and flags the conflict to the admin.

**Acceptance criteria**
- Given a holiday added for tomorrow, when tomorrow's day-close runs, then no absent records are created for it.
- Given leave entered for last week, when saved, then those days change from `absent` to `on_leave` and the change is audited.

### FR-8 Line Manager Team View (M)
**Business rules**
- After login a manager sees a live view of their team for today: not yet in, in, out, absent, on leave.
- They can open any team member's month calendar, daily times and monthly analytics, and their own record.
- Read-only. They can export reports for their own team.

**Acceptance criteria**
- Given a manager with 6 direct reports, when they open the team view, then exactly those 6 appear.
- Given an employee outside their team, when the manager tries to open them through any route, then access is denied.

### FR-9 Analytics and Monthly Review (M)
See section 9 for the metrics and charts. Requirements here:
- Available per employee, per team, per department and company-wide, for any chosen month.
- The system does not label anyone late. It shows each day's clock-in and clock-out times and, as a plain signed number, minutes before or after the official start and end time, so the reviewer can decide.
- At month end, the home screen shows a "Month ready for review" prompt to the admin and managers.

**Acceptance criteria**
- Given a closed month, when the admin opens analytics, then totals match the underlying daily records exactly.
- Given a day with a clock-in 14 minutes after official start, then the report shows "+14 min" with no "late" label.

### FR-10 Audit Log (M)
**Business rules**
- Logged: logins (success and failure), password changes and resets, employee changes, enrollment and deactivation, corrections, leave and holiday changes, settings changes, exports, backups and restores.
- Each entry has who, what, when, the entity, and old and new values where relevant.
- Append-only. The application's database user has find and insert rights on the audit_log collection, with no update or delete privileges.
- The admin can search and filter the log and export it.

**Acceptance criteria**
- Given any correction, then a matching audit entry exists with the old and new values.
- Given an attempt to update or delete an audit document through the app database user, then the database refuses.

### FR-11 Backup and Restore (M)
**Business rules**
- A full database backup runs daily at a configurable time and writes to a local backups folder and a second path, such as an external drive.
- Retention: 30 daily backups and 12 monthly backups, older ones removed automatically.
- Each backup is checksummed. If a backup fails or the second path is missing, a red warning shows on the admin's next login.
- Restore is admin-only, needs password re-entry and a typed confirmation, and takes a safety backup first.

**Acceptance criteria**
- Given the external drive is unplugged, when the backup runs, then the local copy is still made and the admin sees a warning.
- Given a restore from last week's backup in a test environment, then the data matches that day and the app opens normally.

### FR-12 Settings (S)
Organisation name and logo (for reports), working days, official start and end time, day-close time, duplicate-scan window, session timeout, backup times and paths. Every change is audited.

---

## 6. Non-functional Requirements

| Area | Requirement |
|---|---|
| Performance | Match and respond in 2 seconds or less for up to 50 employees with 2 fingers each (about 100 templates). Console screens open in under 2 seconds. |
| Reliability | The app starts automatically with Windows and recovers cleanly after a crash or power cut. MongoDB runs as a local single-node replica set to support multi-document transactions. An accepted scan event and its attendance update commit together with majority write concern and journaling before success is displayed. A single node provides no hardware redundancy; backups remain required. A UPS is recommended for the PC. |
| Availability | No internet dependency. Planned downtime is only for updates and restores. |
| Security | Passwords hashed with Argon2. Fingerprint templates encrypted with AES-256-GCM, key kept outside the database. MongoDB listens on localhost only, with a dedicated low-privilege app user. The app user may read and insert scan events and audit documents but cannot update or delete them. Full-disk encryption (BitLocker) on the PC is recommended. |
| Privacy | Biometric data is sensitive personal data. Collect only templates, never images. Staff are informed and consent is recorded (see section 10). Exports containing personal data are logged. |
| Data integrity | MongoDB unique indexes, including a compound unique index on (employee_id, work_date); collection validators for required fields, BSON types and allowed status values; service-layer validation of document references and clock-out later than clock-in. Related writes use transactions. |
| Usability | Kiosk text readable from 1 metre away. Clear messages in plain English. Console usable with a mouse and keyboard in a few clicks per task. |
| Maintainability | Layered code (UI, services, PyMongo repositories, scanner provider). Versioned Python migration scripts manage MongoDB documents, validators and indexes, recording applied versions in schema_migrations. Unit tests on all business rules. A mock scanner provider so everything can be developed and tested without hardware. |
| Compatibility | Windows 10 or 11, 64-bit. Python 3.12 or newer. |
| Logging | Application errors are written to rotating log files, separate from the audit log. |
| Time | All timestamps stored in UTC and shown in the configured local time zone. |

---

## 7. System Architecture Overview

### 7.1 Overview
A single-machine, layered desktop application. Everything runs on the office PC.

```
+--------------------------- Office PC (Windows) ---------------------------+
|                                                                           |
|  Desktop App (PySide6)                                                    |
|  +-----------------------+   +-----------------------------------------+  |
|  | Kiosk screen          |   | Management console (login required)     |  |
|  | (always listening)    |   | Admin: employees, enrollment, records,   |  |
|  |                       |   |        leave, reports, settings          |  |
|  |                       |   | Manager: team view, analytics, exports   |  |
|  +-----------+-----------+   +--------------------+--------------------+  |
|              |                                    |                       |
|  +-----------v------------------------------------v--------------------+  |
|  | Application services (rules, validation, permissions, audit)        |  |
|  +-----------+------------------------------------+--------------------+  |
|              |                                    |                       |
|  +-----------v-----------+            +-----------v--------------------+  |
|  | Scanner service       |            | Data access (PyMongo)          |  |
|  | FingerprintProvider   |            +-----------+--------------------+  |
|  |  - VendorSdkProvider  |                        |                       |
|  |  - MockProvider (dev) |            +-----------v--------------------+  |
|  +-----------+-----------+            | MongoDB (local replica set)    |  |
|              |                        +-----------+--------------------+  |
|  Kojack USB fingerprint scanner                    |                       |
|                                         Scheduler (day-close, heartbeat,   |
|                                         backups) ----> backup folders      |
+---------------------------------------------------------------------------+
```

### 7.2 Key components
- **Kiosk and console UI:** one PySide6 application. The kiosk is the default screen. Logging in opens the console.
- **Application services:** all business rules live here (clock logic, validation, absence marking, permission checks, audit writes). The UI never talks to the database directly.
- **Scanner service:** runs in its own thread. It loads active templates (decrypted in memory only) into the vendor's matching engine at startup and reloads after any enrollment or deactivation. It talks to hardware through a `FingerprintProvider` interface so the real SDK can be swapped for a mock.
- **Scheduler (APScheduler):** day-close job, heartbeat, daily backup, month-end prompt.
- **Database:** MongoDB on the same machine, bound to localhost and configured as a single-node replica set. PyMongo repositories handle queries, aggregation pipelines and transactions. Provision collection validators, indexes and restricted roles before the app starts; migrations and backup/restore use separate maintenance credentials.
- **Reporting:** ReportLab for PDF, openpyxl for Excel, Qt charts or Matplotlib for on-screen charts.

### 7.3 Technology choices and why

| Choice | Reason |
|---|---|
| MongoDB | Confirmed database for all application data. Collections, validators, unique indexes, aggregation pipelines and replica-set transactions support attendance storage and reporting. Custom roles protect append-only logs. Runs locally without an internet dependency. |
| PyMongo + versioned Python migrations | MongoDB driver for repositories and transactions. Migration scripts version document changes, collection validators and indexes through schema_migrations. |
| PySide6 (Qt) | Native Windows look, good tables and charts, solid threading for the scanner, easy packaging. Chosen over CustomTkinter (less polished tables and charts) and an Electron front end (heavier and needs two runtimes). |
| argon2-cffi, cryptography | Password hashing and template encryption. |
| APScheduler | In-process scheduled jobs. |
| ReportLab, openpyxl | PDF and Excel output without extra software. |
| pytest | Test suite for business rules. |
| PyInstaller + Inno Setup | Single Windows installer. |

### 7.4 Verification options considered

| Option | Accuracy | Lightweight | Verdict |
|---|---|---|---|
| Custom ML model trained on staff fingerprints | Lower than vendor engines, needs many samples per person and retraining for each hire | No | Rejected |
| **Fingerprint template matching via the scanner SDK** | High, vendor-tuned | Yes, no training | **Chosen** |
| Face recognition (embeddings) | Good, but sensitive to lighting and needs anti-spoofing | Medium | Possible later add-on |
| Card or QR plus PIN | Low (buddy punching) | Yes | Possible fallback, out of scope |
| Mobile app with geofence | Medium, easy to spoof | Yes | Not suited to a single office |

### 7.5 Hardware requirement
The selected device is the **Kojack USB fingerprint scanner**, as named by the user. Integrated Biometrics markets a device as **Kojak**; confirm the exact device label, revision and supplied SDK during the hardware spike. Scanner selection is settled; SDK compatibility remains to be validated.

M0 must verify Windows 64-bit capture from Python, quality scoring, template extraction and one-to-many identification. Do not assume the capture SDK includes a matching engine: confirm the available matcher, template format and licence, and integrate a compatible matching SDK if required. Images may exist transiently in memory for extraction but must never be persisted. Build the mock provider alongside the hardware adapter.

Hardware reference: [Integrated Biometrics Kojak](https://integratedbiometrics.com/products/kojak/).

---

## 8. Core MongoDB Collections / Document Schema

Relationships in short: a department has many employees. An employee has one line manager (another employee), many fingerprint templates, many scan events, many daily attendance records, and many leave records. A user account belongs to one employee. Corrections belong to one attendance record.

Each entity below is a MongoDB collection. Documents use `_id` (ObjectId), and references store the related document's ObjectId. The service layer validates referenced documents and business relationships. Timestamps use BSON Date in UTC; calendar dates use `YYYY-MM-DD` strings interpreted in the configured time zone. Allowed string values and required fields are enforced through collection validators. Fields marked unique require explicit unique indexes.

Use a compound unique index on `attendance_records(employee_id, work_date)`. The application role may find and insert `scan_events` and `audit_log` documents but cannot update or delete them. Other collection permissions are granted explicitly; do not grant a broad database-wide readWrite role that overrides these restrictions.

Database references: [MongoDB transactions](https://www.mongodb.com/docs/manual/core/transactions/) and [schema validation](https://www.mongodb.com/docs/manual/core/schema-validation/).

### departments
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| name | String, unique | |
| is_active | Boolean | |
| created_at | Date (UTC) | |

### employees
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| employee_no | String, unique | e.g. EMP-0001 |
| full_name | String | |
| department_id | ObjectId reference to departments | |
| line_manager_id | ObjectId reference to employees, nullable | required for staff |
| phone | String, nullable | |
| status | String, allowed values | active, inactive |
| created_at, deactivated_at | Date (UTC) | |

### users (logins for Main Admin and Line Managers)
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| employee_id | ObjectId reference to employees, unique, nullable | Null for an admin who is not an employee; partial unique index on ObjectId values |
| username | String, unique | |
| password_hash | String | Argon2 |
| role | String, allowed values | main_admin, line_manager |
| must_change_password | Boolean | |
| failed_attempts | Int32 | |
| locked_until | Date (UTC), nullable | |
| is_active | Boolean | |
| last_login_at | Date (UTC) | |

### fingerprint_templates
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| employee_id | ObjectId reference to employees | |
| finger_index | Int32 | 0 to 9 |
| template_encrypted | Binary | encrypted template only |
| template_format | String | SDK name and version |
| quality_score | Int32 | |
| is_active | Boolean | |
| enrolled_by | ObjectId reference to users | |
| enrolled_at | Date (UTC) | |

### scan_events (insert-only raw log)
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| employee_id | ObjectId reference, nullable | null if unrecognised |
| scanned_at | Date (UTC) | |
| outcome | String, allowed values | clock_in, clock_out, rejected_unknown, rejected_duplicate, rejected_day_complete, device_error |
| match_score | Int32, nullable | |

### attendance_records
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| employee_id | ObjectId reference | |
| work_date | String (YYYY-MM-DD) | unique with employee_id |
| department_id_snapshot | ObjectId reference | |
| line_manager_id_snapshot | ObjectId reference, nullable | |
| clock_in_at, clock_out_at | Date (UTC), nullable | Service validation requires clock-out > clock-in |
| minutes_worked | Int32, nullable | |
| status | String, allowed values | present, incomplete, absent, on_leave, system_down |
| day_type | String, allowed values | working, off_day, holiday |
| source | String, allowed values | scanner, manual, system |
| is_edited | Boolean | |
| created_at, updated_at | Date (UTC) | |

### attendance_corrections
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| attendance_record_id | ObjectId reference | |
| changed_by | ObjectId reference to users | |
| field_changed | String | |
| old_value, new_value | String | |
| reason_code | String, allowed values | |
| reason_note | String | |
| changed_at | Date (UTC) | |

### leave_records
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| employee_id | ObjectId reference | |
| start_date, end_date | String (YYYY-MM-DD) | |
| leave_type | String, allowed values | |
| note | String, nullable | |
| recorded_by | ObjectId reference to users | |
| created_at | Date (UTC) | |

### holidays
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| holiday_date | String (YYYY-MM-DD), unique | |
| name | String | |
| recorded_by | ObjectId reference to users | |

### settings
Key-value documents with a unique key and a typed value: working_days, official_start, official_end, day_close_time, duplicate_window_seconds, session_timeout_minutes, backup_time, backup_paths, timezone, organisation_name.

### audit_log (insert-only)
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| actor_user_id | ObjectId reference, nullable | |
| action | String | |
| entity_type, entity_id | String, ObjectId | |
| details | Embedded document | old and new values |
| created_at | Date (UTC) | |

### service_heartbeats
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| beat_at | Date (UTC) | one per minute, pruned after 90 days |

### backups
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| created_at | Date (UTC) | |
| path | String | |
| size_bytes | Int64 | |
| checksum | String | |
| status | String, allowed values | success, failed |

### schema_migrations
| Field | BSON type / validation | Notes |
|---|---|---|
| _id | ObjectId | MongoDB document identifier |
| version | String, unique | Versioned Python migration identifier |
| applied_at | Date (UTC) | Recorded after successful completion |
| checksum | String | Detects changes to an already applied migration |

---

## 9. Reporting & Export

### 9.1 Monthly analytics
**Per employee**
- Working days in the month (after holidays), days present, days absent, days on leave, incomplete days
- Total actual hours and average hours per present day, including time after 17:00; no overtime pay or automatic overtime classification
- Average, earliest and latest clock-in time; average, earliest and latest clock-out time
- Attendance rate = present days divided by (working days minus leave days)
- Daily table with clock-in, clock-out, hours, and signed minutes from official start and end time (no lateness label)

**Per team, department and company**
- Attendance rate, average hours, total absences, incomplete count
- Which weekdays have the most absences
- Ranked lists of attendance rate (highest and lowest) for reviewers

**Charts**
- Daily headcount present across the month (line)
- Attendance rate by department (bar)
- Clock-in time distribution in 30-minute buckets (histogram)
- Month calendar grid per person, colour-coded by status

### 9.2 Standard reports

| Report | Who | Format |
|---|---|---|
| Monthly attendance summary (company, department or team) | Admin, managers (own team) | PDF, Excel |
| Employee monthly attendance sheet | Admin, managers (own team) | PDF, Excel |
| Daily attendance register | Admin | PDF, CSV |
| Absence and leave summary | Admin | Excel |
| Corrections report (what was edited and why) | Admin | PDF, Excel |
| Audit log export | Admin | CSV |
| Raw records export | Admin | CSV |

### 9.3 Export rules
- Files carry the organisation name, report period, generated-by and generated-at, and a note when any included record has been edited.
- Filenames follow `attendance_<type>_<YYYY-MM>.<ext>`.
- Every export is written to the audit log.
- Reports are always computed from current data, so a correction made after a month closes shows up on the next run.

---

## 10. Assumptions & Open Questions

### 10.1 Assumptions
1. The office PC runs Windows 10 or 11 and stays on until the last employee clocks out, including after 17:00. Kojack SDK and matching-engine compatibility with Python must be confirmed during M0.
2. One scanner and one PC for version 1. The Main Admin account is the only account that edits records, and the system allows more than one admin account if later needed.
3. Each person enrolls at least two fingers.
4. Line managers can see their own attendance and their team's. The Main Admin sees everyone.
5. The Main Admin may or may not be an employee who clocks in. The system supports both.
6. A working day is a calendar day. There are no overnight shifts.
7. The PC clock is the time source, and its time zone is set in settings.
8. Biometric data is sensitive personal data. If the workplace is in Nigeria, the Nigeria Data Protection Act 2023 applies, so staff should be informed in writing and consent recorded. Confirm legal obligations with the organisation.
9. Analytics are for human review, so the system carries no lateness or penalty logic.

### 10.2 Open questions (with proposed defaults)

| # | Question | Proposed default |
|---|---|---|
| Q1 | Confirmed scanner; which exact device revision, SDK and matching engine are available? | Kojack selected; verify label/revision, Python integration and matching licence in M0 |
| Q2 | After clock-out, should a later scan the same day be rejected, or replace the clock-out time? | Reject and log it; admin edits if needed |
| Q3 | Which days form the working week? | Monday to Friday remains provisional. Hours are confirmed as 09:00 to 17:00, with later same-day clock-outs allowed |
| Q4 | How long must attendance records be kept? | Keep everything; review after 3 years |
| Q5 | Is signed consent from staff for fingerprint capture required by the organisation? | Yes, store a consent flag and date on the employee |
| Q6 | Does the Main Admin also clock in? | Yes if enrolled |
| Q7 | Where should the second backup copy go (external drive, network share)? | External USB drive |
| Q8 | Database decision (resolved) | MongoDB only, accessed through PyMongo, running as a local single-node replica set |
| Q9 | If the single PC fails, how long can the office go without clocking in? | Restore from backup on a spare PC within one working day |
| Q10 | Should reports hide minutes-from-start figures entirely if reviewers find them unwanted? | Show them, with a setting to hide |

### 10.3 Milestones (indicative, for one developer using an AI coding tool)

| Milestone | Content | Estimate |
|---|---|---|
| M0 Hardware spike | Confirm Kojack device revision, Windows/Python SDK access, template extraction and matching licence; capture, enroll and identify against about 100 templates (50 staff with two fingers each). Build the MockProvider. | 1 week |
| M1 Foundation | Local MongoDB replica set, collections, validators, indexes, PyMongo repositories and versioned migrations; authentication, employees, departments, audit log, settings | 2 weeks |
| M2 Enrollment and kiosk | Enrollment flow, scan pipeline, validation, kiosk feedback, scan events | 2 weeks |
| M3 Records engine | Attendance records, day-close, heartbeat and downtime handling, leave and holidays | 1.5 weeks |
| M4 Corrections and manager view | Admin correction queue, manager team view with access control | 1 week |
| M5 Analytics and reports | Monthly analytics, charts, PDF and Excel exports | 2 weeks |
| M6 Hardening | Backups and restore, encryption and permission checks, installer, error handling | 1.5 weeks |
| M7 Pilot and go-live | UAT with real staff, parallel run alongside the current method for 1 to 2 weeks, fixes, handover | 2 weeks |

Total: roughly 12 to 13 weeks.
