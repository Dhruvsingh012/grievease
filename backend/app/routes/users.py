"""
User Routes - GrievEase v3.0
Student login, Admin login, Staff login, /me endpoint
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import authenticate_admin, authenticate_staff, create_access_token, get_current_user
from app.schemas import StudentCreate, AdminLogin, StaffLogin, Token
from app.models import Admin, Staff, Student
from app import crud

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/student/login", response_model=Token)
def student_login(student_data: StudentCreate, request: Request, db: Session = Depends(get_db)):
    student = crud.create_student(db, student_data)
    token = create_access_token(data={"sub": student.id, "type": "student"})
    crud.log_audit(db, "login", student.admission_number, "student",
                   "student", str(student.id), "Student login",
                   request.client.host if request.client else None)
    return Token(access_token=token, user_role="student")


@router.post("/admin/login", response_model=Token)
def admin_login(login_data: AdminLogin, request: Request, db: Session = Depends(get_db)):
    admin = authenticate_admin(login_data.username, login_data.password, db)
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = create_access_token(data={"sub": admin.id, "type": admin.role})
    crud.log_audit(db, "login", admin.username, admin.role,
                   "admin", str(admin.id), "Admin login",
                   request.client.host if request.client else None)
    return Token(access_token=token, user_role=admin.role)


@router.post("/staff/login", response_model=Token)
def staff_login(login_data: StaffLogin, request: Request, db: Session = Depends(get_db)):
    staff = authenticate_staff(login_data.email, login_data.password, db)
    if not staff:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(data={"sub": staff.id, "type": "staff"})
    crud.log_audit(db, "login", staff.email, "staff",
                   "staff", str(staff.id), "Staff login",
                   request.client.host if request.client else None)
    return Token(access_token=token, user_role="staff")


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    if isinstance(current_user, Admin):
        return {
            "id": current_user.id,
            "type": current_user.role,
            "name": current_user.name or current_user.username,
            "username": current_user.username,
            "email": current_user.email,
        }
    elif isinstance(current_user, Staff):
        return {
            "id": current_user.id,
            "type": "staff",
            "name": current_user.name,
            "email": current_user.email,
            "department": current_user.department,
            "role": current_user.role,
        }
    else:
        return {
            "id": current_user.id,
            "type": "student",
            "name": current_user.name,
            "email": current_user.email,
            "admission_number": current_user.admission_number,
        }


@router.get("/health")
def health():
    return {"status": "ok", "service": "GrievEase", "version": "3.0.0"}
