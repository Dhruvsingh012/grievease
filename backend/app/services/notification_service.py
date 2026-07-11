"""
Notification Service - GrievEase v3.0
Creates DB notifications for all complaint lifecycle events.
"""
from sqlalchemy.orm import Session
from app.models import Admin, Staff, Student, Complaint
from app import crud


def notify_complaint_event(db: Session, complaint: Complaint, event_type: str, triggered_by=None):
    """
    Create notifications for the right recipients based on event type.

    Events:
    - complaint_submitted
    - complaint_assigned
    - complaint_in_progress  (from status "In Progress")
    - complaint_escalated
    - complaint_resolved
    - complaint_closed
    """

    # Find student by admission number for notification
    student = db.query(Student).filter(
        Student.admission_number == complaint.admission_number
    ).first()

    try:
        if event_type == "complaint_submitted":
            # Notify student
            if student:
                crud.create_notification(
                    db, student.id, "student",
                    "Complaint Submitted",
                    f"Your complaint '{complaint.title[:60]}' (ID: {complaint.complaint_id}) has been submitted and auto-assigned.",
                    event_type, complaint.complaint_id
                )
            # Notify assigned staff
            if complaint.assigned_staff_id:
                crud.create_notification(
                    db, complaint.assigned_staff_id, "staff",
                    "New Complaint Assigned",
                    f"A new {complaint.category} complaint has been assigned to you: '{complaint.title[:60]}'",
                    "complaint_assigned", complaint.complaint_id
                )
            # Notify all admins
            _notify_all_admins(db, "New Complaint Received",
                               f"New {complaint.priority} priority {complaint.category} complaint from {complaint.student_name}.",
                               "complaint_submitted", complaint.complaint_id)

        elif event_type in ("complaint_in_progress", "complaint_assigned"):
            if student:
                crud.create_notification(
                    db, student.id, "student",
                    "Complaint In Progress",
                    f"Your complaint '{complaint.title[:60]}' is now being worked on by {complaint.assigned_to or 'our team'}.",
                    event_type, complaint.complaint_id
                )

        elif event_type == "complaint_escalated":
            if student:
                crud.create_notification(
                    db, student.id, "student",
                    "Complaint Escalated",
                    f"Your complaint '{complaint.title[:60]}' has been escalated for faster resolution.",
                    event_type, complaint.complaint_id
                )
            _notify_all_admins(db, "⚠️ Complaint Escalated",
                               f"Complaint {complaint.complaint_id} ({complaint.category}) has been escalated (Level {complaint.escalation_level}).",
                               event_type, complaint.complaint_id)

        elif event_type == "complaint_resolved":
            if student:
                crud.create_notification(
                    db, student.id, "student",
                    "✅ Complaint Resolved",
                    f"Your complaint '{complaint.title[:60]}' has been resolved. Please rate your experience.",
                    event_type, complaint.complaint_id
                )

        elif event_type == "complaint_closed":
            if student:
                crud.create_notification(
                    db, student.id, "student",
                    "Complaint Closed",
                    f"Your complaint '{complaint.title[:60]}' has been closed.",
                    event_type, complaint.complaint_id
                )

    except Exception as e:
        # Notifications are non-critical — never crash the main flow
        print(f"⚠️ Notification error (non-critical): {e}")


def _notify_all_admins(db: Session, title: str, message: str, event_type: str, complaint_id: str):
    admins = db.query(Admin).filter(Admin.is_active == True).all()
    for admin in admins:
        try:
            crud.create_notification(db, admin.id, "admin", title, message, event_type, complaint_id)
        except Exception:
            pass
