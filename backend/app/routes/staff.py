"""
Staff Routes - GrievEase v3.0
Staff management (admin) + Staff dashboard (staff portal)
NOTE: /dashboard/* routes MUST be declared before /{staff_id} to avoid routing conflict.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_admin, get_super_admin, get_current_staff, get_staff_or_admin
from app.schemas import StaffCreate, StaffUpdate, StaffResponse, ComplaintResponse
from app import crud

router = APIRouter(prefix="/api/staff", tags=["staff"])


# ── Staff Dashboard (MUST be before /{staff_id}) ─────────────────────────────

@router.get("/dashboard/me")
def staff_dashboard(
    current_staff=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    """Returns stats summary for the logged-in staff member."""
    complaints = crud.get_complaints_by_staff(db, current_staff.id)
    total     = len(complaints)
    pending   = sum(1 for c in complaints if c.status in ("Pending", "Assigned"))
    in_prog   = sum(1 for c in complaints if c.status == "In Progress")
    resolved  = sum(1 for c in complaints if c.status in ("Resolved", "Closed"))
    escalated = sum(1 for c in complaints if c.status == "Escalated")
    return {
        "staff_name": current_staff.name,
        "department": current_staff.department,
        "stats": {
            "total": total,
            "pending": pending,
            "in_progress": in_prog,
            "resolved": resolved,
            "escalated": escalated,
        },
    }


@router.get("/dashboard/complaints", response_model=List[ComplaintResponse])
def staff_assigned_complaints(
    current_staff=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    """Returns all complaints assigned to the logged-in staff member."""
    return crud.get_complaints_by_staff(db, current_staff.id)


# ── Staff Management (Admin only) ─────────────────────────────────────────────

@router.post("/", response_model=StaffResponse)
def create_staff(
    staff_data: StaffCreate,
    request: Request,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    existing = crud.get_staff_by_email(db, staff_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Staff with this email already exists")
    staff = crud.create_staff(db, staff_data)
    crud.log_audit(
        db, "staff_created", current_admin.username, current_admin.role,
        "staff", str(staff.id), f"Created: {staff.name} ({staff.department})",
        request.client.host if request.client else None,
    )
    return staff


@router.get("/", response_model=List[StaffResponse])
def list_staff(
    active_only: bool = True,
    department: Optional[str] = None,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if department:
        return crud.get_staff_by_department(db, department)
    return crud.get_all_staff(db, active_only=active_only)


@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff_detail(
    staff_id: int,
    current_user=Depends(get_staff_or_admin),
    db: Session = Depends(get_db),
):
    staff = crud.get_staff_by_id(db, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff


@router.put("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: int,
    data: StaffUpdate,
    request: Request,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    staff = crud.update_staff(db, staff_id, data)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    crud.log_audit(
        db, "staff_updated", current_admin.username, current_admin.role,
        "staff", str(staff_id), f"Updated: {staff.name}",
        request.client.host if request.client else None,
    )
    return staff


@router.delete("/{staff_id}")
def deactivate_staff(
    staff_id: int,
    request: Request,
    current_admin=Depends(get_super_admin),
    db: Session = Depends(get_db),
):
    from app.schemas import StaffUpdate
    staff = crud.update_staff(db, staff_id, StaffUpdate(is_active=False))
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    crud.log_audit(
        db, "staff_deactivated", current_admin.username, current_admin.role,
        "staff", str(staff_id), f"Deactivated: {staff.name}",
        request.client.host if request.client else None,
    )
    return {"message": f"Staff {staff.name} deactivated"}
