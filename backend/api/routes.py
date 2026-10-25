"""
REST API.

Live state comes from the in-memory simulation engine; /api/history/* and
/api/analytics read stored records from the database.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.schemas.schemas import (
    AgentCreate, DeployRequest, IncidentCreate, MoveRequest, SensorOverride, SpeedRequest, StepRequest,
)
from backend.services.simulation_service import HISTORY_CATEGORIES, get_service
from agents.agent_types import AGENT_TYPES
from ai.anomaly_detector import model_info
from ai.event_classifier import RULES
from simulation import config

router = APIRouter(prefix="/api", tags=["Environmental Monitoring"])


def svc():
    return get_service()


def _run(fn, *args, **kwargs):
    """Turn engine errors into clear HTTP responses."""
    try:
        return fn(*args, **kwargs)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'\""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ------------------------------------------------------------------ status / state

@router.get("/status")
def get_status():
    return svc().status()


@router.get("/state")
def get_state():
    """Full live snapshot (same payload as the WebSocket 'state' message)."""
    return svc().snapshot()


@router.get("/config")
def get_config():
    return {
        "agent_types": AGENT_TYPES,
        "incident_defaults": config.INCIDENT_DEFAULTS,
        "response_plan": {k: [{"capability": c, "count": n, "optional": o} for c, n, o in v]
                          for k, v in config.RESPONSE_PLAN.items()},
        "classifier_rules": RULES,
        "model": model_info(),
        "comm_range_m": config.COMM_RANGE_M,
        "max_relay_range_m": config.MAX_RELAY_RANGE_M,
        "evidence_range_m": config.EVIDENCE_RANGE_M,
        "consensus_threshold": config.CONSENSUS_THRESHOLD,
        "consensus_min_support": config.CONSENSUS_MIN_SUPPORT,
        "heartbeat_timeout_ticks": config.HEARTBEAT_TIMEOUT_TICKS,
        "telemetry_timeout_ticks": config.TELEMETRY_TIMEOUT_TICKS,
        "demo_location": {"lat": config.DEMO_LATITUDE, "lng": config.DEMO_LONGITUDE, "label": config.DEMO_LABEL},
        "radius_limits_m": [config.MIN_RADIUS_M, config.MAX_RADIUS_M],
        "default_radius_m": config.DEFAULT_RADIUS_M,
        "allowed_speeds": list(config.ALLOWED_SPEEDS),
    }


# ------------------------------------------------------------------ simulation control

@router.post("/simulation/deploy")
def deploy(req: DeployRequest):
    return _run(svc().deploy, req.latitude, req.longitude, req.radius_m, req.label, req.source)


@router.post("/simulation/start")
@router.post("/simulation/resume")
def resume():
    return svc().resume()


@router.post("/simulation/pause")
def pause():
    return svc().pause()


@router.post("/simulation/reset")
def reset():
    return svc().reset()


@router.post("/simulation/speed")
def set_speed(req: SpeedRequest):
    return _run(svc().set_speed, req.speed)


@router.post("/simulation/step")
def step(req: StepRequest = StepRequest()):
    """Advance a fixed number of ticks immediately (useful while paused and for tests)."""
    return svc().step_once(req.ticks)


# ------------------------------------------------------------------ agents

@router.get("/agents")
def list_agents():
    return {"agents": svc().agents()}


@router.post("/agents")
def create_agent(req: AgentCreate):
    return _run(svc().add_agent, req.agent_type, req.agent_id, req.latitude, req.longitude)


@router.get("/agents/{agent_id}")
def agent_detail(agent_id: str):
    return _run(svc().agent_detail, agent_id)


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: str):
    _run(svc().remove_agent, agent_id)
    return {"success": True, "removed": agent_id}


@router.post("/agents/{agent_id}/fail")
def fail_agent(agent_id: str):
    return _run(svc().fail_agent, agent_id)


@router.post("/agents/{agent_id}/restore")
def restore_agent(agent_id: str):
    return _run(svc().restore_agent, agent_id)


@router.post("/agents/{agent_id}/move")
def move_agent(agent_id: str, req: MoveRequest):
    return _run(svc().move_agent, agent_id, req.latitude, req.longitude)


@router.post("/agents/{agent_id}/sensors")
def override_sensors(agent_id: str, req: SensorOverride):
    readings = req.model_dump(exclude={"duration_ticks"}, exclude_none=True)
    if not readings:
        raise HTTPException(status_code=400, detail="Provide at least one sensor value")
    return _run(svc().override_sensors, agent_id, readings, req.duration_ticks)


@router.delete("/agents/{agent_id}/sensors")
def clear_override(agent_id: str):
    return _run(svc().clear_override, agent_id)


@router.get("/agents/{agent_id}/messages")
def agent_messages(agent_id: str, limit: int = Query(100, ge=1, le=500)):
    _run(svc().agent_detail, agent_id)  # 404 if unknown
    return {"messages": svc().live_messages(limit=limit, agent_id=agent_id)}


# ------------------------------------------------------------------ incidents & tasks

@router.post("/incidents")
def create_incident(req: IncidentCreate):
    return _run(svc().create_incident, req.type, req.latitude, req.longitude, req.radius_m, req.severity)


@router.get("/incidents")
def list_incidents():
    return {"incidents": svc().incidents()}


@router.get("/incidents/{incident_id}")
def incident_detail(incident_id: str):
    return _run(svc().incident_detail, incident_id)


@router.get("/tasks")
def list_tasks():
    return {"tasks": svc().tasks()}


# ------------------------------------------------------------------ network & messages

@router.get("/network")
def network():
    return svc().network()


@router.get("/messages")
def live_messages(limit: int = Query(100, ge=1, le=600), type: Optional[str] = None,
                  incident_id: Optional[str] = None, agent_id: Optional[str] = None):
    return {"messages": svc().live_messages(limit, type, incident_id, agent_id)}


# ------------------------------------------------------------------ stored history & analytics

@router.get("/history")
def history(category: str = Query("ALL"), limit: int = Query(200, ge=1, le=1000),
            incident_id: Optional[str] = None, agent_id: Optional[str] = None):
    if category.upper() != "ALL" and category.upper() not in HISTORY_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category. Use ALL or one of {HISTORY_CATEGORIES}")
    return {"history": _run(svc().history, category, limit, incident_id, agent_id), "categories": HISTORY_CATEGORIES}


@router.get("/history/messages")
def stored_messages(limit: int = Query(200, ge=1, le=1000), type: Optional[str] = None,
                    incident_id: Optional[str] = None):
    return {"messages": _run(svc().stored_messages, limit, type, incident_id)}


@router.get("/history/incidents")
def stored_incidents(limit: int = Query(100, ge=1, le=500)):
    return {"incidents": _run(svc().stored_incidents, limit)}


@router.get("/history/incidents/{incident_id}/consensus")
def stored_consensus(incident_id: str):
    return {"rounds": _run(svc().stored_consensus, incident_id)}


@router.get("/history/failures")
def stored_failures(limit: int = Query(100, ge=1, le=500)):
    return {"failures": _run(svc().stored_failures, limit)}


@router.get("/history/task-events")
def stored_task_events(limit: int = Query(200, ge=1, le=1000), incident_id: Optional[str] = None):
    return {"events": _run(svc().stored_task_events, limit, incident_id)}


@router.get("/history/network-events")
def stored_network_events(limit: int = Query(50, ge=1, le=500)):
    return {"events": _run(svc().stored_network_events, limit)}


@router.get("/analytics")
def analytics():
    return _run(svc().analytics)
