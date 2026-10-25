"""
FastAPI application entry point.

    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

Environment variables (optional, see .env.example):
    DATABASE_URL      PostgreSQL/Supabase URL (default: local SQLite file)
    ALLOWED_ORIGINS   comma-separated frontend origins for CORS (default: *)
    SIM_AUTOSTART     0 = do not start the background simulation loop (tests)
    SIM_SEED          integer seed for a reproducible simulation
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.services.simulation_service import get_service
from backend.websocket_manager import ws_manager

AUTOSTART = os.getenv("SIM_AUTOSTART", "1") != "0"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    service = get_service()          # trains the model if needed, loads history, deploys the fleet
    if AUTOSTART:
        await service.start()
    yield
    await service.stop()


app = FastAPI(
    title="Environmental Multi-Agent Monitoring API",
    description="Self-organizing multi-agent simulation for decentralized environmental monitoring.",
    version="3.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Pushes {"type": "state", "data": <snapshot>} every tick. Send "ping" to get "pong"."""
    await ws_manager.connect(websocket)
    try:
        await ws_manager.send(websocket, "state", get_service().snapshot())
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/")
def root():
    return {
        "application": "Self-Organizing Multi-Agent Environmental Monitoring",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws",
    }


@app.get("/health")
def health():
    status = get_service().status()
    return {"status": "ok", "tick": status["simulation"]["tick"], "database_ok": status["database"]["ok"]}
