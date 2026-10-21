import json
from typing import List, Dict, Any
from fastapi import WebSocket


class WebSocketManager:
    """
    Manages active WebSocket client connections and broadcasts
    state changes (telemetry, incidents, network reorganizations, audit logs).
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, data: Any):
        if not self.active_connections:
            return

        payload = {
            "type": event_type,
            "data": data
        }

        # Send asynchronously to all connected clients
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


ws_manager = WebSocketManager()
