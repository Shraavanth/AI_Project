import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.websocket_manager import ws_manager
from backend.database import init_db

# Initialize database schema on startup
init_db()

app = FastAPI(
    title="Environmental Multi-Agent Monitoring API",
    description=(
        "AI-driven decentralized environmental monitoring "
        "with autonomous agents, local consensus, and self-organizing networks."
    ),
    version="2.0.0"
)

# Enable CORS for Next.js frontend (local development + production deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


# ============================================================
# WEBSOCKET REAL-TIME ENDPOINT
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and accept heartbeat pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# ============================================================
# ROOT HEALTHCHECK
# ============================================================

@app.get("/")
def root():
    return {
        "application": "Self-Organizing Multi-Agent Environmental Monitoring",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "status": "/api/status",
            "agents": "/api/agents",
            "network": "/api/network",
            "events": "/api/events",
            "history": "/api/history",
            "analytics": "/api/analytics",
            "websocket": "/ws"
        }
    }