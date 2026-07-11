"""
FastAPI Main Application - GrievEase v3.0
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.database import init_db, get_db
from app.routes import complaints, users, staff, notifications, admin_extra
from app.crud import init_admin, init_departments
from app.websocket_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    print("✅ Database initialized")

    db = next(get_db())
    init_admin(db, settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)
    init_departments(db)
    print(f"✅ Default admin + departments ready")

    os.makedirs("uploads", exist_ok=True)

    yield
    print("👋 Shutting down GrievEase")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered University Grievance Management System — Enterprise Edition",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(users.router)
app.include_router(complaints.router)
app.include_router(staff.router)
app.include_router(notifications.router)
app.include_router(admin_extra.router)


# ── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/{user_type}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_type: str, user_id: int):
    user_key = f"{user_type}:{user_id}"
    await manager.connect(websocket, user_key)
    try:
        await websocket.send_text('{"type":"connected","message":"Real-time updates active"}')
        while True:
            # Keep alive — client can send ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_key)


# ── Escalation Trigger (Admin) ───────────────────────────────────────────────

@app.post("/api/admin/run-escalation")
def run_escalation_now(db=Depends(get_db)):
    from app.services.escalation_service import run_escalation
    result = run_escalation(db)
    return result


# ── Root ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/users/health"
    }

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
