"""
Admin Extra Routes - GrievEase v3.0
Departments, Audit Logs, Reports (CSV), Database Backup
"""
import csv
import io
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_admin, get_super_admin
from app.schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse, AuditLogResponse
from app import crud

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Departments ──────────────────────────────────────────────────────────────

@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return crud.get_all_departments(db)


@router.post("/departments", response_model=DepartmentResponse)
def create_department(
    data: DepartmentCreate,
    request: Request,
    current_admin=Depends(get_super_admin),
    db: Session = Depends(get_db),
):
    dept = crud.create_department(db, data)
    crud.log_audit(db, "department_created", current_admin.username, current_admin.role,
                   "department", str(dept.id), dept.name,
                   request.client.host if request.client else None)
    return dept


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    request: Request,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    dept = crud.update_department(db, dept_id, data)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    crud.log_audit(db, "department_updated", current_admin.username, current_admin.role,
                   "department", str(dept_id), dept.name,
                   request.client.host if request.client else None)
    return dept


# ── Audit Logs ───────────────────────────────────────────────────────────────

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return crud.get_audit_logs(db, skip, limit)


# ── Reports (CSV Export) ─────────────────────────────────────────────────────

@router.get("/reports/complaints/csv")
def export_complaints_csv(
    status_filter: Optional[str] = Query(None, alias="status"),
    category_filter: Optional[str] = Query(None, alias="category"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    complaints = crud.get_complaints_filtered(
        db, status_filter, category_filter, None, None, None, date_from, date_to, 0, 10000
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Complaint ID", "Student Name", "Admission Number", "Email",
        "Title", "Category", "Subcategory", "Priority", "Status",
        "Assigned To", "Department", "Admin Remarks",
        "Rating", "SLA Breached", "Escalation Level",
        "Created At", "Resolved At", "Closed At"
    ])
    for c in complaints:
        writer.writerow([
            c.complaint_id, c.student_name, c.admission_number, c.student_email,
            c.title, c.category, c.subcategory or "", c.priority, c.status,
            c.assigned_to or "", c.assigned_department or "", c.admin_remarks or "",
            c.rating or "", "Yes" if c.sla_breached else "No", c.escalation_level or 0,
            c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
            c.resolved_at.strftime("%Y-%m-%d %H:%M") if c.resolved_at else "",
            c.closed_at.strftime("%Y-%m-%d %H:%M") if c.closed_at else "",
        ])

    output.seek(0)
    filename = f"grievease_complaints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/analytics/json")
def export_analytics_json(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    data = crud.get_analytics(db)
    data["exported_at"] = datetime.now().isoformat()
    output = json.dumps(data, indent=2, default=str)
    filename = f"grievease_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(
        iter([output]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ── Database Backup ──────────────────────────────────────────────────────────

@router.get("/backup")
def backup_database(
    current_admin=Depends(get_super_admin),
    db: Session = Depends(get_db),
):
    """Export all data as JSON backup"""
    from app.models import Complaint, Student, Staff, Department, AuditLog

    def serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    data = {
        "backup_at": datetime.now().isoformat(),
        "complaints": [
            {c: getattr(row, c) for c in row.__table__.columns.keys()}
            for row in db.query(Complaint).all()
        ],
        "students": [
            {c: getattr(row, c) for c in row.__table__.columns.keys()}
            for row in db.query(Student).all()
        ],
        "staff": [
            {k: v for k, v in
             {c: getattr(row, c) for c in row.__table__.columns.keys()}.items()
             if k != "hashed_password"}
            for row in db.query(Staff).all()
        ],
        "departments": [
            {c: getattr(row, c) for c in row.__table__.columns.keys()}
            for row in db.query(Department).all()
        ],
    }

    output = json.dumps(data, default=serialize, indent=2)
    filename = f"grievease_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(
        iter([output]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ── System Stats ─────────────────────────────────────────────────────────────

@router.get("/system/stats")
def system_stats(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    from app.models import Student, Staff, Department, Notification
    return {
        "total_students": db.query(Student).count(),
        "total_staff": db.query(Staff).filter(Staff.is_active == True).count(),
        "total_departments": db.query(Department).count(),
        "unread_notifications": db.query(Notification).filter(Notification.is_read == False).count(),
        "analytics": crud.get_analytics(db),
    }
