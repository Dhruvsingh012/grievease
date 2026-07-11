"""
Email Service - GrievEase v3.0
Sends HTML email on status change. Uses smtplib.
Disabled by default — enable by setting SMTP_USER + SMTP_PASS in .env
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def send_status_email(
    student_email: str,
    student_name: str,
    complaint_id: str,
    complaint_title: str,
    new_status: str,
    admin_remarks: str = None
) -> bool:
    if not settings.EMAIL_ENABLED:
        print(f"📧 Email disabled. Would send to {student_email} — {complaint_id} → {new_status}")
        return False

    try:
        colors = {
            "Pending": "#f59e0b", "Assigned": "#6366f1", "In Progress": "#3b82f6",
            "Escalated": "#ef4444", "Resolved": "#22c55e", "Closed": "#64748b"
        }
        icons = {
            "Pending": "⏳", "Assigned": "📋", "In Progress": "🔄",
            "Escalated": "⚠️", "Resolved": "✅", "Closed": "🔒"
        }
        color = colors.get(new_status, "#64748b")
        icon  = icons.get(new_status, "📋")

        remarks_section = ""
        if admin_remarks:
            remarks_section = f"""
            <div style="background:#f0f9ff;border-left:4px solid #3b82f6;padding:16px;border-radius:8px;margin-top:16px">
              <strong style="color:#1e3a8a">💬 Message from Admin:</strong>
              <p style="margin:8px 0 0;color:#334155">{admin_remarks}</p>
            </div>"""

        html = f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#f5f7fb;margin:0;padding:20px">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1)">
  <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb);padding:28px 32px;text-align:center">
    <h1 style="color:#fff;margin:0;font-size:1.5rem">🎓 GrievEase</h1>
    <p style="color:rgba(255,255,255,.8);margin:6px 0 0;font-size:.9rem">University Grievance Management System</p>
  </div>
  <div style="padding:28px 32px">
    <p style="color:#334155">Dear <strong>{student_name}</strong>,</p>
    <p style="color:#475569">Your complaint status has been updated.</p>
    <div style="text-align:center;margin:24px 0">
      <span style="background:{color};color:#fff;padding:10px 28px;border-radius:999px;font-weight:700;font-size:1rem">{icon} {new_status}</span>
    </div>
    <div style="background:#f8fafc;border-radius:10px;padding:16px;font-size:.9rem;color:#475569">
      <div><strong>Complaint ID:</strong> {complaint_id}</div>
      <div style="margin-top:4px"><strong>Title:</strong> {complaint_title}</div>
      <div style="margin-top:4px"><strong>Status:</strong> <span style="color:{color};font-weight:600">{new_status}</span></div>
    </div>
    {remarks_section}
    <p style="color:#64748b;font-size:.85rem;margin-top:24px">Login to your dashboard to view full details and timeline.</p>
  </div>
  <div style="background:#f8fafc;padding:16px 32px;text-align:center;border-top:1px solid #e2e8f0">
    <p style="color:#94a3b8;font-size:.8rem;margin:0">© 2025 GrievEase | University Grievance Portal<br>Automated message — do not reply.</p>
  </div>
</div></body></html>"""

        plain = f"GrievEase Update\n\nDear {student_name},\nComplaint {complaint_id} ({complaint_title})\nNew Status: {new_status}\n{f'Remarks: {admin_remarks}' if admin_remarks else ''}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[GrievEase] {complaint_id} — Status: {new_status}"
        msg["From"]    = settings.SMTP_FROM
        msg["To"]      = student_email
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, student_email, msg.as_string())

        print(f"✅ Email sent to {student_email}")
        return True

    except Exception as e:
        print(f"⚠️ Email failed (non-critical): {e}")
        return False
