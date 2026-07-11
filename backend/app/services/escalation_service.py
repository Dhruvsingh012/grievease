"""
Escalation Service - GrievEase v3.0
Run periodically (APScheduler or call via /api/admin/run-escalation).
Escalates complaints based on age thresholds.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Complaint
from app import crud


def run_escalation(db: Session) -> dict:
    """
    Check all open complaints and escalate based on age:
      24h  → Level 1: Reminder
       3d  → Level 2: Department Head
       7d  → Level 3: Admin
      15d  → Level 4: Principal
    Returns summary dict.
    """
    now = datetime.utcnow()
    open_statuses = ("Pending", "Assigned", "In Progress")

    complaints = db.query(Complaint).filter(
        Complaint.status.in_(open_statuses)
    ).all()

    counts = {1: 0, 2: 0, 3: 0, 4: 0}

    for c in complaints:
        if not c.created_at:
            continue
        age_hours = (now - c.created_at).total_seconds() / 3600
        age_days  = age_hours / 24

        new_level = c.escalation_level or 0

        if age_days >= 15 and new_level < 4:
            new_level = 4
        elif age_days >= 7 and new_level < 3:
            new_level = 3
        elif age_days >= 3 and new_level < 2:
            new_level = 2
        elif age_hours >= 24 and new_level < 1:
            new_level = 1

        if new_level > (c.escalation_level or 0):
            crud.escalate_complaint(db, c.complaint_id, new_level, "System (Auto-Escalation)")
            counts[new_level] += 1

    total = sum(counts.values())
    print(f"✅ Escalation run complete: {total} complaints escalated. {counts}")
    return {"total_escalated": total, "by_level": counts, "run_at": now.isoformat()}
