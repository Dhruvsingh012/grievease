"""
CRUD Operations - GrievEase v3.0
Upgraded: Staff CRUD, Department CRUD, Notification CRUD, AuditLog CRUD,
          Timeline CRUD, Comment CRUD, SLA logic, Auto-assignment,
          Escalation, Duplicate Detection, Advanced Analytics
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import random

from app.models import (
    Student, Admin, Staff, Department, Complaint,
    ComplaintTimeline, ComplaintComment, Notification, AuditLog
)
from app.schemas import (
    StudentCreate, ComplaintCreate, ComplaintUpdate, ComplaintEdit,
    ComplaintRating, StaffCreate, StaffUpdate, DepartmentCreate,
    DepartmentUpdate, CommentCreate, BulkUpdateRequest
)
from app.auth import get_password_hash


# ==============================================================
# SLA CONFIGURATION (days)
# ==============================================================
SLA_DAYS = {
    "Academic": 5,
    "Administration": 3,
    "Examination": 5,
    "Fees": 3,
    "Hostel": 2,
    "IT Support": 1,
    "Infrastructure": 7,
    "Library": 3,
    "Security": 1,
    "Transport": 3,
}

# Category → Department auto-assignment map
CATEGORY_DEPARTMENT_MAP = {
    "Academic": "Academic Administration",
    "Administration": "Administration Office",
    "Examination": "Examination Cell",
    "Fees": "Accounts Department",
    "Hostel": "Hostel Management",
    "IT Support": "IT Team",
    "Infrastructure": "Maintenance Team",
    "Library": "Library",
    "Security": "Security Office",
    "Transport": "Transport Management",
}


# ==============================================================
# STUDENT
# ==============================================================

def get_student_by_email(db: Session, email: str) -> Optional[Student]:
    return db.query(Student).filter(Student.email == email).first()

def get_student_by_admission(db: Session, admission_number: str) -> Optional[Student]:
    return db.query(Student).filter(Student.admission_number == admission_number).first()

def create_student(db: Session, student: StudentCreate) -> Student:
    existing = get_student_by_email(db, student.email)
    if existing:
        if existing.name != student.name:
            existing.name = student.name
            db.commit()
            db.refresh(existing)
        return existing
    db_s = Student(
        name=student.name,
        email=student.email,
        admission_number=student.admission_number,
        phone=student.phone,
        department=student.department,
        semester=student.semester,
    )
    db.add(db_s)
    db.commit()
    db.refresh(db_s)
    return db_s


# ==============================================================
# ADMIN
# ==============================================================

def get_admin_by_username(db: Session, username: str) -> Optional[Admin]:
    return db.query(Admin).filter(Admin.username == username).first()

def create_admin(db: Session, username: str, password: str, role: str = "admin") -> Admin:
    db_a = Admin(username=username, hashed_password=get_password_hash(password), role=role)
    db.add(db_a)
    db.commit()
    db.refresh(db_a)
    return db_a

def init_admin(db: Session, username: str, password: str):
    if not get_admin_by_username(db, username):
        create_admin(db, username, password, "super_admin")


# ==============================================================
# DEPARTMENT
# ==============================================================

def get_all_departments(db: Session) -> List[Department]:
    return db.query(Department).order_by(Department.name).all()

def get_department_by_id(db: Session, dept_id: int) -> Optional[Department]:
    return db.query(Department).filter(Department.id == dept_id).first()

def get_department_by_name(db: Session, name: str) -> Optional[Department]:
    return db.query(Department).filter(Department.name == name).first()

def create_department(db: Session, dept: DepartmentCreate) -> Department:
    db_d = Department(**dept.model_dump())
    db.add(db_d)
    db.commit()
    db.refresh(db_d)
    return db_d

def update_department(db: Session, dept_id: int, data: DepartmentUpdate) -> Optional[Department]:
    d = get_department_by_id(db, dept_id)
    if not d:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(d, field, value)
    db.commit()
    db.refresh(d)
    return d

def init_departments(db: Session):
    """Create default departments on startup if not exist"""
    defaults = [
        {"name": "Academic Administration", "code": "ACAD", "handles_category": "Academic"},
        {"name": "Administration Office",   "code": "ADMIN", "handles_category": "Administration"},
        {"name": "Examination Cell",        "code": "EXAM",  "handles_category": "Examination"},
        {"name": "Accounts Department",     "code": "ACCT",  "handles_category": "Fees"},
        {"name": "Hostel Management",       "code": "HSTL",  "handles_category": "Hostel"},
        {"name": "IT Team",                 "code": "IT",    "handles_category": "IT Support"},
        {"name": "Maintenance Team",        "code": "MAINT", "handles_category": "Infrastructure"},
        {"name": "Library",                 "code": "LIB",   "handles_category": "Library"},
        {"name": "Security Office",         "code": "SEC",   "handles_category": "Security"},
        {"name": "Transport Management",    "code": "TRANS", "handles_category": "Transport"},
    ]
    for d in defaults:
        if not db.query(Department).filter(Department.code == d["code"]).first():
            db.add(Department(**d))
    db.commit()


# ==============================================================
# STAFF
# ==============================================================

def get_staff_by_email(db: Session, email: str) -> Optional[Staff]:
    return db.query(Staff).filter(Staff.email == email).first()

def get_staff_by_id(db: Session, staff_id: int) -> Optional[Staff]:
    return db.query(Staff).filter(Staff.id == staff_id).first()

def get_all_staff(db: Session, active_only: bool = True) -> List[Staff]:
    q = db.query(Staff)
    if active_only:
        q = q.filter(Staff.is_active == True)
    return q.order_by(Staff.name).all()

def get_staff_by_department(db: Session, department: str) -> List[Staff]:
    return db.query(Staff).filter(
        Staff.department == department,
        Staff.is_active == True
    ).all()

def create_staff(db: Session, staff: StaffCreate) -> Staff:
    db_s = Staff(
        name=staff.name,
        email=staff.email,
        hashed_password=get_password_hash(staff.password),
        department=staff.department,
        department_id=staff.department_id,
        phone=staff.phone,
        designation=staff.designation,
        role=staff.role or "staff",
    )
    db.add(db_s)
    db.commit()
    db.refresh(db_s)
    return db_s

def update_staff(db: Session, staff_id: int, data: StaffUpdate) -> Optional[Staff]:
    s = get_staff_by_id(db, staff_id)
    if not s:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s


# ==============================================================
# COMPLAINT HELPERS
# ==============================================================

def generate_complaint_id() -> str:
    return f"GE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"


def predict_priority(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    critical = ["emergency", "danger", "life", "fire", "assault", "harassment", "attack", "suicide"]
    high = ["urgent", "critical", "immediate", "serious", "broke", "broken", "not working",
            "fail", "failed", "crisis", "stuck", "blocked", "sick", "illness"]
    low  = ["minor", "small", "suggestion", "feedback", "improve", "request",
            "optional", "whenever", "convenient", "informational", "query"]
    for kw in critical:
        if kw in text: return "Critical"
    for kw in high:
        if kw in text: return "High"
    for kw in low:
        if kw in text: return "Low"
    return "Medium"


def get_sla_deadline(category: str) -> datetime:
    days = SLA_DAYS.get(category, 3)
    return datetime.utcnow() + timedelta(days=days)


def auto_assign_department(category: str) -> str:
    return CATEGORY_DEPARTMENT_MAP.get(category, "Administration Office")


def detect_duplicates(db: Session, title: str, description: str, admission_number: str) -> List[str]:
    """Simple duplicate detection: same student, similar title keywords"""
    words = set(title.lower().split())
    stop_words = {"the", "a", "an", "is", "in", "on", "at", "my", "i", "not", "and", "or", "of"}
    key_words = words - stop_words
    if len(key_words) < 2:
        return []

    recent_complaints = db.query(Complaint).filter(
        Complaint.admission_number == admission_number,
        Complaint.status.in_(["Pending", "Assigned", "In Progress"])
    ).order_by(desc(Complaint.created_at)).limit(20).all()

    duplicates = []
    for c in recent_complaints:
        existing_words = set(c.title.lower().split()) - stop_words
        overlap = key_words & existing_words
        if len(overlap) >= max(2, len(key_words) // 2):
            duplicates.append(c.complaint_id)
    return duplicates


# ==============================================================
# COMPLAINT CRUD
# ==============================================================

def create_complaint(
    db: Session,
    complaint: ComplaintCreate,
    predicted_category: str,
    file_path: str = None
) -> Complaint:
    priority = complaint.priority or predict_priority(complaint.title, complaint.description)
    assigned_dept = auto_assign_department(predicted_category)
    sla_deadline = get_sla_deadline(predicted_category)

    # Find staff in that department to auto-assign
    dept_staff = get_staff_by_department(db, assigned_dept)
    assigned_staff_id = dept_staff[0].id if dept_staff else None
    assigned_to = dept_staff[0].name if dept_staff else None

    status = "Assigned" if assigned_to else "Pending"

    db_c = Complaint(
        complaint_id=generate_complaint_id(),
        student_name=complaint.student_name,
        student_email=complaint.student_email,
        admission_number=complaint.admission_number,
        title=complaint.title,
        description=complaint.description,
        category=predicted_category,
        subcategory=complaint.subcategory,
        priority=priority,
        status=status,
        assigned_department=assigned_dept,
        assigned_staff_id=assigned_staff_id,
        assigned_to=assigned_to,
        file_path=file_path,
        sla_deadline=sla_deadline,
    )
    db.add(db_c)
    db.flush()  # get db_c.id

    # Add timeline entry
    timeline_event = "Assigned" if assigned_to else "Submitted"
    desc_text = f"Complaint submitted by {complaint.student_name}."
    if assigned_to:
        desc_text += f" Auto-assigned to {assigned_to} ({assigned_dept})."
    add_timeline_entry(db, db_c.id, db_c.complaint_id, timeline_event, desc_text, "System", "system")

    db.commit()
    db.refresh(db_c)
    return db_c


def get_complaint_by_id(db: Session, complaint_id: str) -> Optional[Complaint]:
    return db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()

def get_all_complaints(db: Session, skip=0, limit=200) -> List[Complaint]:
    return db.query(Complaint).order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()

def get_complaints_by_student(db: Session, admission_number: str, skip=0, limit=200) -> List[Complaint]:
    return db.query(Complaint).filter(
        Complaint.admission_number == admission_number
    ).order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()

def get_complaints_by_staff(db: Session, staff_id: int, skip=0, limit=200) -> List[Complaint]:
    return db.query(Complaint).filter(
        Complaint.assigned_staff_id == staff_id
    ).order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()

def get_complaints_by_status(db: Session, status: str, skip=0, limit=200) -> List[Complaint]:
    return db.query(Complaint).filter(
        Complaint.status == status
    ).order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()

def get_complaints_by_category(db: Session, category: str, skip=0, limit=200) -> List[Complaint]:
    return db.query(Complaint).filter(
        Complaint.category == category
    ).order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()

def get_complaints_filtered(
    db: Session,
    status: str = None,
    category: str = None,
    priority: str = None,
    department: str = None,
    staff_id: int = None,
    date_from: datetime = None,
    date_to: datetime = None,
    skip: int = 0,
    limit: int = 200
) -> List[Complaint]:
    q = db.query(Complaint)
    if status:       q = q.filter(Complaint.status == status)
    if category:     q = q.filter(Complaint.category == category)
    if priority:     q = q.filter(Complaint.priority == priority)
    if department:   q = q.filter(Complaint.assigned_department == department)
    if staff_id:     q = q.filter(Complaint.assigned_staff_id == staff_id)
    if date_from:    q = q.filter(Complaint.created_at >= date_from)
    if date_to:      q = q.filter(Complaint.created_at <= date_to)
    return q.order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()


def update_complaint_status(
    db: Session,
    complaint_id: str,
    update_data: ComplaintUpdate,
    performed_by: str = "Admin",
    performed_by_role: str = "admin"
) -> Optional[Complaint]:
    c = get_complaint_by_id(db, complaint_id)
    if not c:
        return None

    old_status = c.status
    c.status = update_data.status

    if update_data.admin_remarks is not None:
        c.admin_remarks = update_data.admin_remarks
    if update_data.internal_notes is not None:
        c.internal_notes = update_data.internal_notes
    if update_data.priority is not None:
        c.priority = update_data.priority
    if update_data.assigned_to is not None:
        c.assigned_to = update_data.assigned_to
    if update_data.assigned_staff_id is not None:
        c.assigned_staff_id = update_data.assigned_staff_id
    if update_data.assigned_department is not None:
        c.assigned_department = update_data.assigned_department

    now = datetime.utcnow()
    if update_data.status == "Resolved" and not c.resolved_at:
        c.resolved_at = now
    elif update_data.status == "Closed":
        if not c.closed_at:
            c.closed_at = now
        if not c.resolved_at:
            c.resolved_at = now
    elif update_data.status not in ("Resolved", "Closed"):
        c.resolved_at = None

    # Check SLA breach
    if c.sla_deadline and now > c.sla_deadline and update_data.status not in ("Resolved", "Closed"):
        c.sla_breached = True

    # Timeline
    desc_text = f"Status changed from {old_status} to {update_data.status}."
    if update_data.admin_remarks:
        desc_text += f" Remarks: {update_data.admin_remarks}"
    if update_data.assigned_to:
        desc_text += f" Assigned to: {update_data.assigned_to}"
    add_timeline_entry(db, c.id, complaint_id, update_data.status, desc_text, performed_by, performed_by_role)

    db.commit()
    db.refresh(c)
    return c


def edit_complaint(
    db: Session,
    complaint_id: str,
    edit_data: ComplaintEdit,
    admission_number: str
) -> Optional[Complaint]:
    c = get_complaint_by_id(db, complaint_id)
    if not c or c.admission_number != admission_number or c.status not in ("Pending", "Assigned"):
        return None
    if edit_data.title:       c.title = edit_data.title
    if edit_data.description: c.description = edit_data.description
    db.commit()
    db.refresh(c)
    return c


def rate_complaint(
    db: Session,
    complaint_id: str,
    rating_data: ComplaintRating,
    admission_number: str
) -> Optional[Complaint]:
    c = get_complaint_by_id(db, complaint_id)
    if not c or c.admission_number != admission_number or c.status not in ("Resolved", "Closed"):
        return None
    c.rating = rating_data.rating
    if rating_data.rating_feedback:
        c.rating_feedback = rating_data.rating_feedback
    db.commit()
    db.refresh(c)
    return c


def bulk_update_complaints(
    db: Session,
    complaint_ids: List[str],
    status: str,
    admin_remarks: str = None,
    performed_by: str = "Admin"
) -> int:
    count = 0
    now = datetime.utcnow()
    for cid in complaint_ids:
        c = get_complaint_by_id(db, cid)
        if c:
            old = c.status
            c.status = status
            if admin_remarks: c.admin_remarks = admin_remarks
            if status == "Resolved" and not c.resolved_at: c.resolved_at = now
            elif status == "Closed":
                if not c.closed_at: c.closed_at = now
            elif status not in ("Resolved", "Closed"):    c.resolved_at = None
            add_timeline_entry(db, c.id, cid, status, f"Bulk update: {old} → {status}", performed_by, "admin")
            count += 1
    db.commit()
    return count


def delete_all_complaints(db: Session):
    db.query(ComplaintTimeline).delete()
    db.query(ComplaintComment).delete()
    db.query(Complaint).delete()
    db.commit()


# ==============================================================
# TIMELINE
# ==============================================================

def add_timeline_entry(
    db: Session,
    complaint_db_id: int,
    complaint_id: str,
    event: str,
    description: str = None,
    performed_by: str = "System",
    performed_by_role: str = "system"
):
    entry = ComplaintTimeline(
        complaint_db_id=complaint_db_id,
        complaint_id=complaint_id,
        event=event,
        description=description,
        performed_by=performed_by,
        performed_by_role=performed_by_role,
    )
    db.add(entry)
    # Do not commit here — caller commits


def get_complaint_timeline(db: Session, complaint_id: str) -> List[ComplaintTimeline]:
    return db.query(ComplaintTimeline).filter(
        ComplaintTimeline.complaint_id == complaint_id
    ).order_by(ComplaintTimeline.created_at).all()


# ==============================================================
# COMMENTS
# ==============================================================

def add_comment(
    db: Session,
    complaint_id: str,
    comment: CommentCreate,
    author_name: str,
    author_role: str
) -> Optional[ComplaintComment]:
    c = get_complaint_by_id(db, complaint_id)
    if not c:
        return None
    # Students cannot add internal notes
    is_internal = comment.is_internal and author_role in ("staff", "admin", "super_admin")
    db_comment = ComplaintComment(
        complaint_db_id=c.id,
        complaint_id=complaint_id,
        author_name=author_name,
        author_role=author_role,
        comment_text=comment.comment_text,
        is_internal=is_internal,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comments(db: Session, complaint_id: str, include_internal: bool = False) -> List[ComplaintComment]:
    q = db.query(ComplaintComment).filter(ComplaintComment.complaint_id == complaint_id)
    if not include_internal:
        q = q.filter(ComplaintComment.is_internal == False)
    return q.order_by(ComplaintComment.created_at).all()


# ==============================================================
# NOTIFICATIONS
# ==============================================================

def create_notification(
    db: Session,
    recipient_id: int,
    recipient_type: str,
    title: str,
    message: str,
    event_type: str,
    complaint_id: str = None
) -> Notification:
    n = Notification(
        recipient_id=recipient_id,
        recipient_type=recipient_type,
        title=title,
        message=message,
        event_type=event_type,
        complaint_id=complaint_id,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def get_notifications(
    db: Session,
    recipient_id: int,
    recipient_type: str,
    unread_only: bool = False,
    limit: int = 50
) -> List[Notification]:
    q = db.query(Notification).filter(
        Notification.recipient_id == recipient_id,
        Notification.recipient_type == recipient_type,
    )
    if unread_only:
        q = q.filter(Notification.is_read == False)
    return q.order_by(desc(Notification.created_at)).limit(limit).all()


def mark_notifications_read(db: Session, recipient_id: int, recipient_type: str):
    db.query(Notification).filter(
        Notification.recipient_id == recipient_id,
        Notification.recipient_type == recipient_type,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()


def get_unread_count(db: Session, recipient_id: int, recipient_type: str) -> int:
    return db.query(Notification).filter(
        Notification.recipient_id == recipient_id,
        Notification.recipient_type == recipient_type,
        Notification.is_read == False
    ).count()


# ==============================================================
# AUDIT LOG
# ==============================================================

def log_audit(
    db: Session,
    action: str,
    performed_by: str,
    performed_by_role: str,
    target_type: str = None,
    target_id: str = None,
    details: str = None,
    ip_address: str = None
):
    entry = AuditLog(
        action=action,
        performed_by=performed_by,
        performed_by_role=performed_by_role,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()


def get_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> List[AuditLog]:
    return db.query(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


# ==============================================================
# STATISTICS & ANALYTICS
# ==============================================================

def get_complaint_statistics(db: Session) -> dict:
    total       = db.query(Complaint).count()
    pending     = db.query(Complaint).filter(Complaint.status == "Pending").count()
    assigned    = db.query(Complaint).filter(Complaint.status == "Assigned").count()
    in_progress = db.query(Complaint).filter(Complaint.status == "In Progress").count()
    resolved    = db.query(Complaint).filter(Complaint.status == "Resolved").count()
    escalated   = db.query(Complaint).filter(Complaint.status == "Escalated").count()
    closed      = db.query(Complaint).filter(Complaint.status == "Closed").count()
    cat_stats   = db.query(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
    pri_stats   = db.query(Complaint.priority, func.count(Complaint.id)).group_by(Complaint.priority).all()
    return {
        "total": total, "pending": pending + assigned, "in_progress": in_progress,
        "resolved": resolved, "escalated": escalated, "closed": closed,
        "by_category": {c: n for c, n in cat_stats},
        "by_priority": {p: n for p, n in pri_stats},
    }


def get_analytics(db: Session) -> dict:
    total    = db.query(Complaint).count()
    resolved = db.query(Complaint).filter(Complaint.status.in_(["Resolved", "Closed"])).count()
    escalated= db.query(Complaint).filter(Complaint.status == "Escalated").count()

    cat_data = db.query(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
    pri_data = db.query(Complaint.priority, func.count(Complaint.id)).group_by(Complaint.priority).all()
    sts_data = db.query(Complaint.status,   func.count(Complaint.id)).group_by(Complaint.status).all()

    monthly = db.query(
        func.strftime("%Y-%m", Complaint.created_at).label("month"),
        func.count(Complaint.id).label("count")
    ).group_by("month").order_by("month").all()

    # SQLite-compatible: get all complaints and aggregate in Python
    all_dept_complaints = db.query(
        Complaint.assigned_department,
        Complaint.status,
        func.count(Complaint.id).label("cnt")
    ).group_by(Complaint.assigned_department, Complaint.status).all()

    from collections import defaultdict
    dept_agg = defaultdict(lambda: {"total": 0, "resolved": 0, "escalated": 0})
    for row in all_dept_complaints:
        dept = row[0] or "Unassigned"
        status = row[1]
        cnt = row[2]
        dept_agg[dept]["total"] += cnt
        if status in ("Resolved", "Closed"):
            dept_agg[dept]["resolved"] += cnt
        if status == "Escalated":
            dept_agg[dept]["escalated"] += cnt
    dept_data = [(k, v["total"], v["resolved"], v["escalated"]) for k, v in dept_agg.items()]

    resolved_list = db.query(Complaint).filter(
        Complaint.status.in_(["Resolved", "Closed"]),
        Complaint.resolved_at != None
    ).all()
    avg_days = 0
    if resolved_list:
        days = [(c.resolved_at - c.created_at).days for c in resolved_list if c.resolved_at and c.resolved_at > c.created_at]
        avg_days = round(sum(days) / len(days), 1) if days else 0

    sla_breached = db.query(Complaint).filter(Complaint.sla_breached == True).count()

    ratings = db.query(func.avg(Complaint.rating)).filter(Complaint.rating != None).scalar()
    avg_rating = round(float(ratings), 2) if ratings else 0

    # Staff performance
    # Staff performance - SQLite safe
    staff_all = db.query(Complaint.assigned_to, Complaint.status).filter(
        Complaint.assigned_to != None
    ).all()
    from collections import defaultdict as _dd
    sp = _dd(lambda: {"total": 0, "resolved": 0})
    for row in staff_all:
        sp[row[0]]["total"] += 1
        if row[1] in ("Resolved", "Closed"):
            sp[row[0]]["resolved"] += 1
    staff_perf = [(k, v["total"], v["resolved"]) for k, v in sorted(sp.items(), key=lambda x: -x[1]["total"])[:10]]

    return {
        "total": total,
        "resolved": resolved,
        "escalated": escalated,
        "sla_breached": sla_breached,
        "resolution_rate": round(resolved / total * 100, 1) if total else 0,
        "avg_resolution_days": avg_days,
        "avg_rating": avg_rating,
        "by_category": [{"category": c, "count": n} for c, n in cat_data],
        "by_priority": [{"priority": p, "count": n} for p, n in pri_data],
        "by_status":   [{"status": s,   "count": n} for s, n in sts_data],
        "monthly_trend": [{"month": m, "count": c} for m, c in monthly][-6:],
        "department_performance": [
            {
                "department": d or "Unassigned",
                "total": t,
                "resolved": int(r or 0),
                "escalated": int(e or 0),
                "resolution_rate": round(int(r or 0) / t * 100, 1) if t else 0,
            } for d, t, r, e in dept_data
        ],
        "staff_performance": [
            {"staff": s, "total": t, "resolved": int(r or 0)} for s, t, r in staff_perf
        ],
    }


def get_escalation_candidates(db: Session) -> List[Complaint]:
    """Return complaints that need escalation based on age"""
    now = datetime.utcnow()
    return db.query(Complaint).filter(
        Complaint.status.in_(["Pending", "Assigned", "In Progress"]),
        Complaint.sla_deadline < now,
        Complaint.sla_breached == False
    ).all()


def escalate_complaint(db: Session, complaint_id: str, level: int, performed_by: str = "System"):
    c = get_complaint_by_id(db, complaint_id)
    if not c:
        return
    c.escalation_level = level
    c.status = "Escalated"
    c.escalated_at = datetime.utcnow()
    c.sla_breached = True
    level_labels = {1: "Reminder sent", 2: "Escalated to Department Head", 3: "Escalated to Admin", 4: "Escalated to Principal"}
    desc = level_labels.get(level, f"Escalated to level {level}")
    add_timeline_entry(db, c.id, complaint_id, "Escalated", desc, performed_by, "system")
    db.commit()
