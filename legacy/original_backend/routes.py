from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.services.simulation_service import simulation_service
from backend.schemas.schemas import (
    AgentDeploymentRequest,
    AgentCreate,
    AgentUpdate,
    EventTriggerRequest
)

router = APIRouter(
    prefix="/api",
    tags=["Environmental Monitoring"]
)


# ============================================================
# SYSTEM STATUS
# ============================================================

@router.get("/status")
def get_status():
    return simulation_service.get_status()


# ============================================================
# AGENTS
# ============================================================

@router.get("/agents")
def get_agents():
    return {
        "agents": simulation_service.get_agents()
    }


@router.get("/agents/deployment")
def get_agent_deployment():
    return {"deployment": simulation_service.get_deployment()}


@router.post("/agents/deploy")
def deploy_agents(deployment: AgentDeploymentRequest):
    try:
        return simulation_service.deploy_agents(
            latitude=deployment.latitude,
            longitude=deployment.longitude,
            radius_km=deployment.radius_km,
            area_label=deployment.area_label,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/agents/{agent_id}")
def get_agent_detail(agent_id: str):
    agent = simulation_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")
    return agent


@router.post("/agents")
def create_agent(agent_data: AgentCreate):
    try:
        new_agent = simulation_service.add_agent(agent_data.model_dump(exclude_unset=True))
        return {
            "success": True,
            "message": f"Agent {new_agent['id']} created successfully.",
            "agent": new_agent
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/agents/{agent_id}")
def update_agent(agent_id: str, updates: AgentUpdate):
    agent = simulation_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")

    update_dict = updates.model_dump(exclude_unset=True)
    if not update_dict:
        return agent

    # Handle coordinates change if provided
    if "x" in update_dict or "y" in update_dict:
        new_x = update_dict.get("x", agent["position"][0])
        new_y = update_dict.get("y", agent["position"][1])
        simulation_service.move_agent(agent_id, new_x, new_y)

    # Handle sensor updates
    sensor_keys = ["temperature", "humidity", "smoke", "co2", "air_quality", "soil_moisture", "battery"]
    readings = {k: update_dict[k] for k in sensor_keys if k in update_dict}
    if readings:
        updated = simulation_service.update_agent_sensors(agent_id, readings)
        return updated

    return simulation_service.get_agent(agent_id)


@router.post("/agents/{agent_id}/move-direction")
def move_agent_direction(agent_id: str, direction: str = Query(..., description="UP, DOWN, LEFT, or RIGHT")):
    agent = simulation_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")

    res = simulation_service.move_agent_direction(agent_id, direction)
    return {
        "success": True,
        "agent": res
    }


@router.post("/simulation/patrol-step")
def simulation_patrol_step():
    return simulation_service.step_patrol()



@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: str):
    success = simulation_service.remove_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")
    return {
        "success": True,
        "message": f"Agent {agent_id} deleted successfully."
    }


@router.post("/agents/{agent_id}/fail")
def fail_agent(agent_id: str):
    agent = simulation_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")
    if agent["status"] == "FAILED":
        raise HTTPException(status_code=400, detail=f"Agent {agent_id} is already in FAILED state.")

    failed = simulation_service.fail_agent(agent_id)
    return {
        "success": True,
        "failed_agent": agent_id,
        "agent": failed
    }


@router.post("/agents/{agent_id}/restore")
def restore_agent(agent_id: str):
    agent = simulation_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")
    if agent["status"] == "ACTIVE":
        raise HTTPException(status_code=400, detail=f"Agent {agent_id} is already ACTIVE.")

    restored = simulation_service.restore_agent(agent_id)
    return {
        "success": True,
        "restored_agent": agent_id,
        "agent": restored
    }


@router.post("/agents/{agent_id}/restart")
def restart_agent(agent_id: str):
    agent = simulation_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")
    restarted = simulation_service.restart_agent(agent_id)
    return {
        "success": True,
        "restarted_agent": agent_id,
        "agent": restarted
    }


@router.post("/agents/{agent_id}/analyze")
def trigger_agent_analysis(agent_id: str):
    agent = simulation_service.model.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")

    res = agent.analyze_environment()
    simulation_service._sync_all_agents_to_db()
    return {
        "agent_id": agent_id,
        "ai_result": res,
        "ai_explanation": agent.get_ai_explanation()
    }


# ============================================================
# ENVIRONMENTAL EVENTS / INCIDENTS
# ============================================================

@router.post("/events/fire")
def create_fire_event(req: Optional[EventTriggerRequest] = None):
    return simulation_service.trigger_event(
        event_type="FIRE",
        center_x=req.center_x if req and req.center_x is not None else 10,
        center_y=req.center_y if req and req.center_y is not None else 10,
        radius=req.radius if req and req.radius is not None else 3,
        target_agent_id=req.target_agent_id if req else None,
        latitude=req.latitude if req else None,
        longitude=req.longitude if req else None,
        zone_name=req.zone_name if req else None
    )


@router.post("/events/pollution")
def create_pollution_event(req: Optional[EventTriggerRequest] = None):
    return simulation_service.trigger_event(
        event_type="POLLUTION",
        center_x=req.center_x if req and req.center_x is not None else 10,
        center_y=req.center_y if req and req.center_y is not None else 10,
        radius=req.radius if req and req.radius is not None else 3,
        target_agent_id=req.target_agent_id if req else None,
        latitude=req.latitude if req else None,
        longitude=req.longitude if req else None,
        zone_name=req.zone_name if req else None
    )


@router.post("/events/extreme-heat")
def create_extreme_heat_event(req: Optional[EventTriggerRequest] = None):
    return simulation_service.trigger_event(
        event_type="EXTREME_HEAT",
        center_x=req.center_x if req and req.center_x is not None else 10,
        center_y=req.center_y if req and req.center_y is not None else 10,
        radius=req.radius if req and req.radius is not None else 3,
        target_agent_id=req.target_agent_id if req else None,
        latitude=req.latitude if req else None,
        longitude=req.longitude if req else None,
        zone_name=req.zone_name if req else None
    )


@router.get("/events")
def get_events():
    return {
        "events": simulation_service.get_events()
    }


@router.get("/events/{event_id}/communications")
def get_event_communications(event_id: str):
    return {
        "event_id": event_id,
        "communications": simulation_service.get_event_communications(event_id)
    }


@router.post("/events/{event_id}/resolve")
def resolve_event(event_id: str):
    return simulation_service.resolve_event(event_id)


@router.post("/events/{event_id}/acknowledge")
def acknowledge_event(event_id: str):
    return simulation_service.acknowledge_event(event_id)


@router.post("/agents/recharge")
def recharge_fleet():
    return simulation_service.recharge_fleet()


# ============================================================
# NETWORK & SELF-ORGANIZATION
# ============================================================

@router.get("/network")
def get_network():
    return simulation_service.get_network()


@router.post("/network/recover")
def recover_network():
    return simulation_service.recover_network()


# ============================================================
# SIMULATION RESET & AGENT FAIL HELPER
# ============================================================

@router.post("/simulation/reset")
def reset_simulation():
    return simulation_service.reset()


@router.post("/agents/fail-fire-agent")
def fail_fire_agent():
    return simulation_service.fail_fire_agent()


# ============================================================
# AUDIT LOG HISTORY & ANALYTICS
# ============================================================

@router.get("/history")
def get_history(
    category: str = Query("ALL", description="Filter category: ALL, EVENT, ANOMALIES, CONSENSUS, FAILURES, RECOVERY, NETWORK, AGENTS"),
    limit: int = Query(100, ge=1, le=500)
):
    return {
        "history": simulation_service.get_history(category=category, limit=limit)
    }


@router.get("/analytics")
def get_analytics():
    return simulation_service.get_analytics()