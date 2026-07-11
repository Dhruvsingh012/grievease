"""
Authentication - GrievEase v3.0
Upgraded: Staff auth, role-based dependencies (get_current_staff, get_super_admin)
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Admin, Student, Staff
from app.schemas import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        user_type: str = payload.get("type")
        if not user_id_str or not user_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return TokenData(user_id=int(user_id_str), user_type=user_type)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_admin(username: str, password: str, db: Session) -> Optional[Admin]:
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.hashed_password):
        return None
    return admin


def authenticate_staff(email: str, password: str, db: Session) -> Optional[Staff]:
    staff = db.query(Staff).filter(Staff.email == email, Staff.is_active == True).first()
    if not staff or not verify_password(password, staff.hashed_password):
        return None
    return staff


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Returns Admin, Staff, or Student based on token type"""
    token_data = decode_token(credentials.credentials)

    if token_data.user_type in ("admin", "super_admin"):
        user = db.query(Admin).filter(Admin.id == token_data.user_id).first()
    elif token_data.user_type == "staff":
        user = db.query(Staff).filter(Staff.id == token_data.user_id).first()
    elif token_data.user_type == "student":
        user = db.query(Student).filter(Student.id == token_data.user_id).first()
    else:
        user = None

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_admin(current_user=Depends(get_current_user)):
    """Allows admin OR super_admin"""
    if not isinstance(current_user, Admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def get_super_admin(current_user=Depends(get_current_user)):
    """Only super_admin"""
    if not isinstance(current_user, Admin) or current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin access required")
    return current_user


def get_current_staff(current_user=Depends(get_current_user)):
    """Staff only"""
    if not isinstance(current_user, Staff):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")
    return current_user


def get_staff_or_admin(current_user=Depends(get_current_user)):
    """Staff OR Admin"""
    if not isinstance(current_user, (Staff, Admin)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff or Admin access required")
    return current_user
