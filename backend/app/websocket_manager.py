"""
WebSocket Manager - GrievEase v3.0
Real-time notifications via WebSocket.
"""
from typing import Dict, List
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        # Maps user_key (e.g. "admin:1", "student:5") → list of WebSocket connections
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_key: str):
        await websocket.accept()
        if user_key not in self.active:
            self.active[user_key] = []
        self.active[user_key].append(websocket)
        print(f"🔌 WebSocket connected: {user_key} (total: {len(self.active[user_key])})")

    def disconnect(self, websocket: WebSocket, user_key: str):
        if user_key in self.active:
            self.active[user_key] = [ws for ws in self.active[user_key] if ws != websocket]
            if not self.active[user_key]:
                del self.active[user_key]
        print(f"🔌 WebSocket disconnected: {user_key}")

    async def send_to_user(self, user_key: str, data: dict):
        """Send message to all connections of a specific user"""
        if user_key in self.active:
            dead = []
            for ws in self.active[user_key]:
                try:
                    await ws.send_text(json.dumps(data))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active[user_key].remove(ws)

    async def broadcast_to_role(self, role: str, data: dict):
        """Broadcast to all connections of a given role prefix (admin, staff, student)"""
        for key in list(self.active.keys()):
            if key.startswith(f"{role}:"):
                await self.send_to_user(key, data)

    async def broadcast_all(self, data: dict):
        for key in list(self.active.keys()):
            await self.send_to_user(key, data)


# Singleton
manager = ConnectionManager()
