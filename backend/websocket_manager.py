"""
Keeps track of connected WebSocket clients and pushes state updates to them.
"""

from typing import Any, List

from fastapi import WebSocket


class WebSocketManager:

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send(self, websocket: WebSocket, event_type: str, data: Any):
        await websocket.send_json({"type": event_type, "data": data})

    async def broadcast(self, event_type: str, data: Any):
        if not self.active_connections:
            return
        payload = {"type": event_type, "data": data}
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection)


ws_manager = WebSocketManager()
