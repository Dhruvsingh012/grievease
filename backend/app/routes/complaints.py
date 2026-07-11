"""
Complaint Routes - GrievEase v3.0
Handles: CRUD, AI prediction, bulk ops, analytics, comments, timeline, SLA
"""
import os
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, get_current_admin, get_staff_or_admin
from app.models import Student, Admin, Staff
from app.schemas import (
    ComplaintCreate, ComplaintUpdate, ComplaintEdit, ComplaintRating,
    ComplaintResponse, ComplaintStats, BulkUpdateRequest, CommentCreate, CommentResponse
)
from app import crud
from app.nlp import predict_category
from app.services.notification_service import notify_complaint_event
from app.services.email_service import send_status_email

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _actor_info(user):
    """Returns (name, role) tuple from any user type."""
    if isinstance(user, Admin):
        return (user.name or user.username, user.role)
    elif isinstance(user, Staff):
        return (user.name, "staff")
    else:
        return (getattr(user, "name", "Student"), "student")


# ── Fixed paths MUST be declared before /{complaint_id} ──────────────────────

@router.get("/stats", response_model=ComplaintStats)
def get_stats(db: Session = Depends(get_db)):
    """Public endpoint — used on landing page for live counters."""
    return crud.get_complaint_statistics(db)


@router.get("/analytics")
def get_analytics(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return crud.get_analytics(db)


@router.get("/predict-category")
def predict_complaint_category(
    text: str = Query(..., min_length=3),
    current_user=Depends(get_current_user),
):
    """AI prediction — returns predicted category + priority + confidence."""
    category = predict_category(text)
    priority = crud.predict_priority(text, "")
    confidence = 0.85
    try:
        from app.nlp import MODEL_LOADED, model, vectorizer
        if MODEL_LOADED and model and vectorizer:
            proba = model.predict_proba(vectorizer.transform([text]))[0]
            confidence = round(float(proba.max()), 2)
    except Exception:
        pass
    return {
        "predicted_category": category,
        "confidence": confidence,
        "predicted_priority": priority,
    }


@router.post("/bulk-update")
def bulk_update(
    payload: BulkUpdateRequest,
    request: Request,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    actor, role = _actor_info(current_admin)
    count = crud.bulk_update_complaints(
        db, payload.complaint_ids, payload.new_status, payload.admin_remarks, actor
    )
    crud.log_audit(
        db, "bulk_update", actor, role, "complaint",
        ",".join(payload.complaint_ids),
        f"Bulk → {payload.new_status} ({count} complaints)",
        request.client.host if request.client else None,
    )
    return {"updated": count, "status": payload.new_status}


@router.post("/json", response_model=ComplaintResponse)
def submit_complaint_json(
    complaint: ComplaintCreate,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, Student):
        if current_user.admission_number != complaint.admission_number:
            raise HTTPException(status_code=403, detail="You can only submit for your own account")

    dupes = crud.detect_duplicates(db, complaint.title, complaint.description, complaint.admission_number)
    if dupes:
        raise HTTPException(
            status_code=409,
            detail={"message": "Similar complaint already exists.", "duplicate_ids": dupes},
        )

    text = f"{complaint.title} {complaint.description}"
    predicted_category = complaint.category if complaint.category else predict_category(text)
    db_complaint = crud.create_complaint(db, complaint, predicted_category)
    notify_complaint_event(db, db_complaint, "complaint_submitted", current_user)
    crud.log_audit(
        db, "complaint_created", complaint.admission_number, "student",
        "complaint", db_complaint.complaint_id, complaint.title,
        request.client.host if request.client else None,
    )
    return db_complaint


@router.delete("/clear-all")
def clear_all(
    request: Request,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    actor, role = _actor_info(current_admin)
    crud.delete_all_complaints(db)
    crud.log_audit(db, "bulk_delete", actor, role, "complaint", "all",
                   "Cleared all complaints", request.client.host if request.client else None)
    return {"message": "All complaints deleted"}


# ── Collection ────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ComplaintResponse])
def get_complaints(
    skip: int = 0,
    limit: int = 200,
    status_filter: Optional[str] = Query(None, alias="status"),
    category_filter: Optional[str] = Query(None, alias="category"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    department_filter: Optional[str] = Query(None, alias="department"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, Admin):
        return crud.get_complaints_filtered(
            db, status_filter, category_filter, priority_filter,
            department_filter, None, date_from, date_to, skip, limit,
        )
    elif isinstance(current_user, Staff):
        return crud.get_complaints_by_staff(db, current_user.id, skip, limit)
    elif isinstance(current_user, Student):
        return crud.get_complaints_by_student(db, current_user.admission_number, skip, limit)
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/", response_model=ComplaintResponse)
async def submit_complaint_multipart(
    student_name: str = Form(...),
    student_email: str = Form(...),
    admission_number: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    category: Optional[str] = Form(None),
    subcategory: Optional[str] = Form(None),
    priority: str = Form("Medium"),
    file: Optional[UploadFile] = File(None),
    request: Request = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, Student):
        if current_user.admission_number != admission_number:
            raise HTTPException(status_code=403, detail="You can only submit for your own account")

    dupes = crud.detect_duplicates(db, title, description, admission_number)
    if dupes:
        raise HTTPException(
            status_code=409,
            detail={"message": "Similar complaint already exists.", "duplicate_ids": dupes},
        )

    file_path = None
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type {ext} not allowed.")
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Max 5MB.")
        unique_name = f"{uuid.uuid4()}{ext}"
        save_path = os.path.join(UPLOAD_DIR, unique_name)
        with open(save_path, "wb") as f_out:
            f_out.write(content)
        file_path = save_path

    text = f"{title} {description}"
    predicted_category = category if category else predict_category(text)
    complaint_data = ComplaintCreate(
        student_name=student_name, student_email=student_email,
        admission_number=admission_number, title=title,
        description=description, category=predicted_category,
        subcategory=subcategory, priority=priority,
    )
    db_complaint = crud.create_complaint(db, complaint_data, predicted_category, file_path)
    notify_complaint_event(db, db_complaint, "complaint_submitted", current_user)
    crud.log_audit(
        db, "complaint_created", admission_number, "student",
        "complaint", db_complaint.complaint_id, title,
        request.client.host if request and request.client else None,
    )
    return db_complaint


# ── Single complaint — dynamic route MUST be last ────────────────────────────

@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_single_complaint(
    complaint_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    complaint = crud.get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if isinstance(current_user, Student):
        if complaint.admission_number != current_user.admission_number:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif isinstance(current_user, Staff):
        if complaint.assigned_staff_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your assigned complaint")
    return complaint


@router.put("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(
    complaint_id: str,
    update_data: ComplaintUpdate,
    request: Request,
    current_user=Depends(get_staff_or_admin),
    db: Session = Depends(get_db),
):
    actor, role = _actor_info(current_user)
    if isinstance(current_user, Staff):
        c = crud.get_complaint_by_id(db, complaint_id)
        if not c or c.assigned_staff_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your assigned complaint")

    complaint = crud.update_complaint_status(db, complaint_id, update_data, actor, role)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    notify_complaint_event(
        db, complaint,
        f"complaint_{update_data.status.lower().replace(' ', '_')}",
        current_user,
    )
    if update_data.status in ("Resolved", "Closed"):
        send_status_email(
            complaint.student_email, complaint.student_name,
            complaint.complaint_id, complaint.title,
            update_data.status, update_data.admin_remarks,
        )
    crud.log_audit(
        db, "status_changed", actor, role, "complaint", complaint_id,
        f"→ {update_data.status}", request.client.host if request.client else None,
    )
    return complaint


@router.patch("/{complaint_id}/edit", response_model=ComplaintResponse)
def edit_complaint(
    complaint_id: str,
    edit_data: ComplaintEdit,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not isinstance(current_user, Student):
        raise HTTPException(status_code=403, detail="Only students can edit complaints")
    complaint = crud.edit_complaint(db, complaint_id, edit_data, current_user.admission_number)
    if not complaint:
        raise HTTPException(status_code=400, detail="Cannot edit: not found, not yours, or not Pending/Assigned")
    return complaint


@router.post("/{complaint_id}/rate", response_model=ComplaintResponse)
def rate_complaint(
    complaint_id: str,
    rating_data: ComplaintRating,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not isinstance(current_user, Student):
        raise HTTPException(status_code=403, detail="Only students can rate complaints")
    complaint = crud.rate_complaint(db, complaint_id, rating_data, current_user.admission_number)
    if not complaint:
        raise HTTPException(status_code=400, detail="Cannot rate: not resolved yet")
    return complaint


@router.get("/{complaint_id}/comments", response_model=List[CommentResponse])
def get_comments(
    complaint_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    include_internal = isinstance(current_user, (Admin, Staff))
    return crud.get_comments(db, complaint_id, include_internal)


@router.post("/{complaint_id}/comments", response_model=CommentResponse)
def add_comment(
    complaint_id: str,
    comment: CommentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    actor, role = _actor_info(current_user)
    result = crud.add_comment(db, complaint_id, comment, actor, role)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return result


@router.get("/{complaint_id}/timeline")
def get_timeline(
    complaint_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    timeline = crud.get_complaint_timeline(db, complaint_id)
    return [
        {
            "id": t.id,
            "event": t.event,
            "description": t.description,
            "performed_by": t.performed_by,
            "performed_by_role": t.performed_by_role,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in timeline
    ]
