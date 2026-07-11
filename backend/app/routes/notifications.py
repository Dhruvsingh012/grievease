"""
Notification Routes - GrievEase v3.0
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.auth import get_current_user
from app.models import Admin, Staff, Student
from app.schemas import NotificationResponse
from app import crud

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, Admin):
        rtype = "admin"
    elif isinstance(current_user, Staff):
        rtype = "staff"
    else:
        rtype = "student"
    return crud.get_notifications(db, current_user.id, rtype, unread_only)


@router.get("/unread-count")
def unread_count(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, Admin):   rtype = "admin"
    elif isinstance(current_user, Staff): rtype = "staff"
    else:                                  rtype = "student"
    count = crud.get_unread_count(db, current_user.id, rtype)
    return {"count": count}


@router.post("/mark-read")
def mark_read(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, Admin):   rtype = "admin"
    elif isinstance(current_user, Staff): rtype = "staff"
    else:                                  rtype = "student"
    crud.mark_notifications_read(db, current_user.id, rtype)
    return {"message": "All notifications marked as read"}
