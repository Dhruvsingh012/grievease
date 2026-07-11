"""
SQLAlchemy ORM Models - GrievEase v3.0
Upgraded: Staff, Notification, AuditLog, ComplaintComment, ComplaintTimeline, Department
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


# ==================== STUDENT ====================

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    admission_number = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    semester = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Student {self.admission_number}: {self.name}>"


# ==================== ADMIN ====================

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), default="admin")  # admin | super_admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Admin {self.username} [{self.role}]>"


# ==================== DEPARTMENT ====================

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    head_name = Column(String(100), nullable=True)
    head_email = Column(String(100), nullable=True)
    handles_category = Column(String(50), nullable=True)  # Which complaint category this dept handles
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    staff = relationship("Staff", back_populates="department_rel")

    def __repr__(self):
        return f"<Department {self.code}: {self.name}>"


# ==================== STAFF ====================

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), default="staff")   # staff | department_head
    department = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    phone = Column(String(20), nullable=True)
    designation = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    department_rel = relationship("Department", back_populates="staff")

    def __repr__(self):
        return f"<Staff {self.email}: {self.department}>"


# ==================== COMPLAINT ====================

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(50), unique=True, index=True, nullable=False)

    # Student Info
    student_name = Column(String(100), nullable=False)
    student_email = Column(String(100), nullable=False)
    admission_number = Column(String(50), nullable=False, index=True)

    # Complaint Details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)

    # Priority & Status
    priority = Column(String(20), default="Medium")    # Low | Medium | High | Critical
    status = Column(String(30), default="Pending", index=True)
    # Pending | Assigned | In Progress | Escalated | Resolved | Closed

    # Assignment
    assigned_to = Column(String(100), nullable=True)        # staff name
    assigned_staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    assigned_department = Column(String(100), nullable=True)

    # Admin/Staff fields
    admin_remarks = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)   # Only visible to staff/admin

    # File attachment
    file_path = Column(String(500), nullable=True)

    # Rating
    rating = Column(Integer, nullable=True)
    rating_feedback = Column(Text, nullable=True)

    # SLA
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    sla_breached = Column(Boolean, default=False)

    # Escalation
    escalation_level = Column(Integer, default=0)   # 0=none, 1=reminder, 2=dept_head, 3=admin, 4=principal
    escalated_at = Column(DateTime(timezone=True), nullable=True)

    # Duplicate detection
    duplicate_of = Column(String(50), nullable=True)  # complaint_id of original

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    timeline = relationship("ComplaintTimeline", back_populates="complaint", cascade="all, delete-orphan")
    comments = relationship("ComplaintComment", back_populates="complaint", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Complaint {self.complaint_id}: {self.status}>"


# ==================== COMPLAINT TIMELINE ====================

class ComplaintTimeline(Base):
    __tablename__ = "complaint_timeline"

    id = Column(Integer, primary_key=True, index=True)
    complaint_db_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    complaint_id = Column(String(50), nullable=False)
    event = Column(String(100), nullable=False)         # Submitted | Assigned | In Progress | Escalated | Resolved | Closed
    description = Column(Text, nullable=True)
    performed_by = Column(String(100), nullable=True)   # username or "System"
    performed_by_role = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    complaint = relationship("Complaint", back_populates="timeline")

    def __repr__(self):
        return f"<Timeline {self.complaint_id}: {self.event}>"


# ==================== COMPLAINT COMMENT ====================

class ComplaintComment(Base):
    __tablename__ = "complaint_comments"

    id = Column(Integer, primary_key=True, index=True)
    complaint_db_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    complaint_id = Column(String(50), nullable=False)
    author_name = Column(String(100), nullable=False)
    author_role = Column(String(30), nullable=False)    # student | staff | admin
    comment_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)        # Internal notes - only staff/admin can see
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    complaint = relationship("Complaint", back_populates="comments")

    def __repr__(self):
        return f"<Comment by {self.author_name} on {self.complaint_id}>"


# ==================== NOTIFICATION ====================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, nullable=False)
    recipient_type = Column(String(20), nullable=False)  # student | staff | admin
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    event_type = Column(String(50), nullable=False)
    # complaint_submitted | complaint_assigned | complaint_escalated | complaint_resolved | complaint_closed
    complaint_id = Column(String(50), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Notification {self.event_type} -> {self.recipient_type}:{self.recipient_id}>"


# ==================== AUDIT LOG ====================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    # login | logout | complaint_created | status_changed | assigned | escalated | deleted | bulk_update
    performed_by = Column(String(100), nullable=False)
    performed_by_role = Column(String(30), nullable=False)
    target_type = Column(String(50), nullable=True)   # complaint | user | staff | department
    target_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.performed_by}>"
