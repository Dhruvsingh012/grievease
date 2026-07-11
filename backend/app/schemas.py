"""
Pydantic Schemas - GrievEase v3.0
Upgraded: Staff, Department, Notification, AuditLog, Timeline, Comment schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ==================== STUDENT ====================

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    admission_number: str = Field(..., min_length=3, max_length=50)
    phone: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None


class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    admission_number: str
    phone: Optional[str]
    department: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== ADMIN ====================

class AdminLogin(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)


class AdminResponse(BaseModel):
    id: int
    username: str
    name: Optional[str]
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== DEPARTMENT ====================

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=20)
    head_name: Optional[str] = None
    head_email: Optional[str] = None
    handles_category: Optional[str] = None


class DepartmentUpdate(BaseModel):
    head_name: Optional[str] = None
    head_email: Optional[str] = None
    handles_category: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str
    head_name: Optional[str]
    head_email: Optional[str]
    handles_category: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== STAFF ====================

class StaffCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    department: str = Field(..., min_length=2)
    department_id: Optional[int] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    role: Optional[str] = "staff"


class StaffLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)


class StaffUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None


class StaffResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: str
    phone: Optional[str]
    designation: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== COMPLAINT ====================

class ComplaintCreate(BaseModel):
    student_name: str = Field(..., min_length=2, max_length=100)
    student_email: EmailStr
    admission_number: str = Field(..., min_length=3, max_length=50)
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[str] = "Medium"


class ComplaintUpdate(BaseModel):
    """Admin/Staff update"""
    status: str = Field(..., pattern="^(Pending|Assigned|In Progress|Escalated|Resolved|Closed)$")
    admin_remarks: Optional[str] = None
    internal_notes: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(Low|Medium|High|Critical)$")
    assigned_to: Optional[str] = None
    assigned_staff_id: Optional[int] = None
    assigned_department: Optional[str] = None


class ComplaintEdit(BaseModel):
    """Student edit — only while Pending"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10)


class ComplaintRating(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    rating_feedback: Optional[str] = None


# ---- Sub-schemas for nested responses ----

class TimelineEntry(BaseModel):
    id: int
    event: str
    description: Optional[str]
    performed_by: Optional[str]
    performed_by_role: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    id: int
    author_name: str
    author_role: str
    comment_text: str
    is_internal: bool
    created_at: datetime
    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=2)
    is_internal: bool = False


class ComplaintResponse(BaseModel):
    id: int
    complaint_id: str
    student_name: str
    student_email: str
    admission_number: str
    title: str
    description: str
    category: str
    subcategory: Optional[str]
    priority: str
    status: str
    admin_remarks: Optional[str]
    internal_notes: Optional[str]
    assigned_to: Optional[str]
    assigned_staff_id: Optional[int]
    assigned_department: Optional[str]
    file_path: Optional[str]
    rating: Optional[int]
    rating_feedback: Optional[str]
    sla_deadline: Optional[datetime]
    sla_breached: Optional[bool]
    escalation_level: Optional[int]
    escalated_at: Optional[datetime]
    duplicate_of: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    timeline: Optional[List[TimelineEntry]] = []
    comments: Optional[List[CommentResponse]] = []
    class Config:
        from_attributes = True


class ComplaintStats(BaseModel):
    total: int
    pending: int
    in_progress: int
    resolved: int
    escalated: int = 0
    closed: int = 0
    by_category: dict
    by_priority: dict


# ==================== NOTIFICATION ====================

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    event_type: str
    complaint_id: Optional[str]
    is_read: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== AUDIT LOG ====================

class AuditLogResponse(BaseModel):
    id: int
    action: str
    performed_by: str
    performed_by_role: str
    target_type: Optional[str]
    target_id: Optional[str]
    details: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# ==================== BULK OPS ====================

class BulkUpdateRequest(BaseModel):
    complaint_ids: List[str]
    new_status: str = Field(..., pattern="^(Pending|Assigned|In Progress|Escalated|Resolved|Closed)$")
    admin_remarks: Optional[str] = None


# ==================== AUTH ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_role: Optional[str] = None


class TokenData(BaseModel):
    user_id: int
    user_type: str   # student | staff | admin | super_admin


# ==================== ANALYTICS ====================

class DepartmentPerformance(BaseModel):
    department: str
    total: int
    resolved: int
    escalated: int
    avg_resolution_days: float
    resolution_rate: float
