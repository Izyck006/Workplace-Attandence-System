import os
import re
import smtplib
import logging
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger(__name__)
LAGOS = timezone(timedelta(hours=1))
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email_address(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_smtp_configured() -> bool:
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    return bool(host and user)


def get_smtp_config():
    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587").strip() or 587),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from_addr": os.getenv("SMTP_FROM", "Randaframes Attendance <noreply@randaframes.com>").strip(),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes"),
        "use_ssl": os.getenv("SMTP_USE_SSL", "false").lower() in ("true", "1", "yes") or int(os.getenv("SMTP_PORT", "587") or 587) == 465,
    }


def send_email(to_addrs: list[str], subject: str, html_content: str, text_content: str = "") -> dict:
    valid_recipients = [addr.strip() for addr in to_addrs if validate_email_address(addr.strip())]
    if not valid_recipients:
        return {"success": False, "error": "No valid recipient email addresses provided.", "sent_to": []}

    config = get_smtp_config()
    if not config["host"]:
        log.warning("SMTP not configured. Digest email to %s logged but not sent over network.", valid_recipients)
        return {
            "success": False,
            "simulated": True,
            "sent_to": valid_recipients,
            "message": "SMTP host not configured in .env. Email body was generated and logged.",
        }

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["from_addr"]
    msg["To"] = ", ".join(valid_recipients)

    if text_content:
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if config["use_ssl"]:
            server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=20)
        else:
            server = smtplib.SMTP(config["host"], config["port"], timeout=20)
            if config["use_tls"]:
                server.starttls()

        if config["user"] and config["password"]:
            server.login(config["user"], config["password"])

        server.sendmail(config["from_addr"], valid_recipients, msg.as_string())
        server.quit()
        log.info("Successfully sent email '%s' to %s", subject, valid_recipients)
        return {"success": True, "sent_to": valid_recipients, "message": f"Email delivered to {len(valid_recipients)} recipient(s)."}
    except Exception as exc:
        log.error("Failed to send email to %s: %s", valid_recipients, exc)
        return {"success": False, "error": str(exc), "sent_to": valid_recipients}


def build_morning_digest(db, target_date: str = None) -> dict:
    if not target_date:
        now_lagos = datetime.now(timezone.utc).astimezone(LAGOS)
        target_date = now_lagos.strftime("%Y-%m-%d")

    # Fetch all active employees
    active_employees = list(db.employees.find({"status": "active"}))
    total_staff = len(active_employees)

    # Fetch today's attendance records
    attendance_records = list(db.attendance_records.find({"work_date": target_date}))
    checked_in_emp_ids = {str(rec.get("employee_id")) for rec in attendance_records if rec.get("clock_in_at")}
    timed_out_emp_ids = {str(rec.get("employee_id")) for rec in attendance_records if rec.get("clock_out_at")}

    # Group by office
    from src.offices import OFFICE_MAP
    offices_stats = {}
    for emp in active_employees:
        off_id = emp.get("office_id", "unknown")
        if off_id not in offices_stats:
            off_name = OFFICE_MAP.get(off_id, {}).get("name", off_id)
            location = OFFICE_MAP.get(off_id, {}).get("location", "Other")
            offices_stats[off_id] = {
                "name": off_name,
                "location": location,
                "total": 0,
                "present": 0,
                "absent": 0,
                "timed_out": 0,
                "present_names": [],
                "absent_names": [],
            }

        stats = offices_stats[off_id]
        stats["total"] += 1
        emp_id_str = str(emp.get("_id"))
        emp_name = emp.get("full_name") or f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()

        if emp_id_str in checked_in_emp_ids:
            stats["present"] += 1
            if emp_id_str in timed_out_emp_ids:
                stats["timed_out"] += 1
            stats["present_names"].append(emp_name)
        else:
            stats["absent"] += 1
            stats["absent_names"].append(emp_name)

    total_present = sum(s["present"] for s in offices_stats.values())
    total_absent = sum(s["absent"] for s in offices_stats.values())
    rate = round((total_present / total_staff * 100), 1) if total_staff else 0.0

    # Format HTML table rows
    rows_html = ""
    for off_id, s in sorted(offices_stats.items(), key=lambda x: x[1]["name"]):
        pct = round(s["present"] / s["total"] * 100, 1) if s["total"] else 0
        rows_html += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 10px 14px; font-weight: 600; color: #111827;">{s['name']}</td>
            <td style="padding: 10px 14px; color: #6b7280;">{s['location']}</td>
            <td style="padding: 10px 14px; text-align: center; color: #374151;">{s['total']}</td>
            <td style="padding: 10px 14px; text-align: center; font-weight: 600; color: #16a34a;">{s['present']}</td>
            <td style="padding: 10px 14px; text-align: center; font-weight: 600; color: #dc2626;">{s['absent']}</td>
            <td style="padding: 10px 14px; text-align: center; font-weight: 600; color: #2563eb;">{pct}%</td>
        </tr>
        """

    # Format absent staff section
    absent_sections_html = ""
    for off_id, s in sorted(offices_stats.items(), key=lambda x: x[1]["name"]):
        if s["absent_names"]:
            names_list = ", ".join(s["absent_names"])
            absent_sections_html += f"""
            <div style="margin-bottom: 10px; font-size: 13px;">
                <strong style="color: #4b5563;">{s['name']} ({len(s['absent_names'])}):</strong>
                <span style="color: #ef4444;"> {names_list}</span>
            </div>
            """

    if not absent_sections_html:
        absent_sections_html = "<p style='color: #16a34a; font-size: 13px;'>All active staff across all offices have checked in today!</p>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; padding: 24px; margin: 0;">
        <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e5e7eb;">
            <div style="background: linear-gradient(135deg, #1e3a8a, #2563eb); padding: 24px 30px; color: #ffffff;">
                <h1 style="margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.5px;">Randaframes Attendance</h1>
                <p style="margin: 4px 0 0 0; font-size: 14px; opacity: 0.9;">Daily Morning Executive Attendance Digest &bull; {target_date}</p>
            </div>

            <div style="padding: 24px 30px;">
                <div style="display: flex; gap: 12px; margin-bottom: 24px;">
                    <div style="flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center;">
                        <div style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase;">Total Staff</div>
                        <div style="font-size: 24px; font-weight: 700; color: #0f172a; margin-top: 4px;">{total_staff}</div>
                    </div>
                    <div style="flex: 1; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px; text-align: center;">
                        <div style="font-size: 12px; font-weight: 600; color: #166534; text-transform: uppercase;">Present</div>
                        <div style="font-size: 24px; font-weight: 700; color: #16a34a; margin-top: 4px;">{total_present}</div>
                    </div>
                    <div style="flex: 1; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 14px; text-align: center;">
                        <div style="font-size: 12px; font-weight: 600; color: #991b1b; text-transform: uppercase;">Not In Yet</div>
                        <div style="font-size: 24px; font-weight: 700; color: #dc2626; margin-top: 4px;">{total_absent}</div>
                    </div>
                    <div style="flex: 1; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 14px; text-align: center;">
                        <div style="font-size: 12px; font-weight: 600; color: #1e40af; text-transform: uppercase;">Turnout</div>
                        <div style="font-size: 24px; font-weight: 700; color: #2563eb; margin-top: 4px;">{rate}%</div>
                    </div>
                </div>

                <h3 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600; color: #1f2937;">Branch Breakdown</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 24px;">
                    <thead>
                        <tr style="background: #f9fafb; border-bottom: 2px solid #e5e7eb; color: #4b5563; text-align: left;">
                            <th style="padding: 10px 14px;">Office Name</th>
                            <th style="padding: 10px 14px;">Location</th>
                            <th style="padding: 10px 14px; text-align: center;">Staff</th>
                            <th style="padding: 10px 14px; text-align: center;">Present</th>
                            <th style="padding: 10px 14px; text-align: center;">Not In</th>
                            <th style="padding: 10px 14px; text-align: center;">Rate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>

                <h3 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600; color: #1f2937;">Staff Pending Check-in</h3>
                <div style="background: #fafafa; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px;">
                    {absent_sections_html}
                </div>

                <p style="margin-top: 24px; font-size: 11px; color: #9ca3af; text-align: center;">
                    Generated automatically by Randaframes Central Attendance System &bull; Lagos Time: {datetime.now(timezone.utc).astimezone(LAGOS).strftime("%H:%M:%S")}
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""Randaframes Attendance - Morning Digest ({target_date})
==================================================
Total Staff: {total_staff} | Present: {total_present} | Absent/Pending: {total_absent} | Turnout: {rate}%

Branch Breakdown:
"""
    for off_id, s in sorted(offices_stats.items(), key=lambda x: x[1]["name"]):
        text_content += f"- {s['name']} ({s['location']}): {s['present']}/{s['total']} present ({s['absent']} absent)\n"

    return {
        "date": target_date,
        "total_staff": total_staff,
        "total_present": total_present,
        "total_absent": total_absent,
        "turnout_rate": rate,
        "html": html_content,
        "text": text_content,
        "offices_stats": offices_stats,
    }
