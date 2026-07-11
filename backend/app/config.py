"""
Configuration - GrievEase v3.0
All settings loaded from environment variables with safe defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./grievease.db")

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

    # ── Admin Defaults ────────────────────────────────────────────────────────
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    # ── App Info ──────────────────────────────────────────────────────────────
    APP_NAME: str = os.getenv("APP_NAME", "GrievEase")
    APP_VERSION: str = os.getenv("APP_VERSION", "3.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # ── CORS — covers localhost dev ports + production frontend ───────────────
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")

    @property
    def ALLOWED_ORIGINS(self) -> list:
        origins = [
            "http://localhost:3000",    "http://127.0.0.1:3000",
            "http://localhost:5500",    "http://127.0.0.1:5500",
            "http://localhost:5501",    "http://127.0.0.1:5501",
            "http://localhost:5502",    "http://127.0.0.1:5502",
            "http://localhost:8000",    "http://127.0.0.1:8000",
            "http://localhost:8080",    "http://127.0.0.1:8080",
            "null",  # file:// protocol
        ]
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL)
        return origins

    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str  = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int  = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str  = os.getenv("SMTP_USER", "")
    SMTP_PASS: str  = os.getenv("SMTP_PASS", "")
    SMTP_FROM: str  = os.getenv("SMTP_FROM", "GrievEase <noreply@grievease.com>")
    EMAIL_ENABLED: bool = os.getenv("SMTP_USER", "") != ""

    # ── File Uploads ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str       = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
    ALLOWED_EXTENSIONS: list = ["jpg", "jpeg", "png", "pdf", "doc", "docx"]

    # ── App Constants ─────────────────────────────────────────────────────────
    COMPLAINT_CATEGORIES = [
        "Academic", "Administration", "Examination", "Fees", "Hostel",
        "IT Support", "Infrastructure", "Library", "Security", "Transport"
    ]
    STATUS_OPTIONS  = ["Pending", "Assigned", "In Progress", "Escalated", "Resolved", "Closed"]
    PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]

    # ── Escalation Thresholds ─────────────────────────────────────────────────
    ESCALATION_REMINDER_HOURS: int  = 24
    ESCALATION_DEPT_HEAD_DAYS: int  = 3
    ESCALATION_ADMIN_DAYS: int      = 7
    ESCALATION_PRINCIPAL_DAYS: int  = 15


settings = Settings()
