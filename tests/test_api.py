"""FastAPI routes, WebSocket and database persistence (temporary SQLite database)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.simulation_service import SimulationService, get_service
from simulation.geo import offset


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        c.post("/api/simulation/reset")
        yield c


def test_root_status_state(client):
    assert client.get("/").json()["status"] == "running"
    status = client.get("/api/status").json()
    assert status["stats"]["total_agents"] == 20
    assert status["database"]["ok"] is True
    state = client.get("/api/state").json()
    assert {"agents", "incidents", "links", "network", "stats", "site", "simulation"} <= state.keys()
    agent = state["agents"][0]
    assert {"lat", "lng", "status", "battery", "readings", "ai", "neighbors", "task_id"} <= agent.keys()


def test_config_endpoint(client):
    cfg = client.get("/api/config").json()
    assert set(cfg["agent_types"]) == {"MONITOR_DRONE", "FIRE_DRONE", "SPRINKLER", "POLLUTION_UNIT", "COOLING_UNIT"}


def test_simulation_controls(client):
    assert client.post("/api/simulation/pause").json()["running"] is False
    assert client.post("/api/simulation/speed", json={"speed": 2.0}).json()["speed"] == 2.0
    assert client.post("/api/simulation/speed", json={"speed": 3.0}).status_code == 400
    tick = client.get("/api/status").json()["simulation"]["tick"]
    assert client.post("/api/simulation/step", json={"ticks": 3}).json()["tick"] == tick + 3
    assert client.post("/api/simulation/resume").json()["running"] is True
    client.post("/api/simulation/pause")


def test_deploy_moves_area(client):
    res = client.post("/api/simulation/deploy", json={"latitude": 13.0827, "longitude": 80.2707,
                                                      "radius_m": 1500, "label": "Chennai", "source": "SEARCH"})
    assert res.status_code == 200
    data = res.json()
    assert data["site"]["label"] == "Chennai" and data["site"]["source"] == "SEARCH"
    assert abs(data["agents"][0]["lat"] - 13.08) < 0.05
    assert client.post("/api/simulation/deploy", json={"latitude": 13, "longitude": 80, "radius_m": 50}).status_code == 422
    client.post("/api/simulation/deploy", json={"latitude": 12.9692, "longitude": 79.1559, "radius_m": 1200,
                                                "label": "VIT", "source": "DEMO"})


def test_agent_endpoints_and_errors(client):
    assert client.get("/api/agents").json()["agents"]
    detail = client.get("/api/agents/MD-01").json()
    assert detail["type"] == "MONITOR_DRONE" and "patrol_route" in detail
    assert client.get("/api/agents/NOPE").status_code == 404
    assert client.post("/api/agents/NOPE/fail").status_code == 404
    assert client.post("/api/agents/MD-03/restore").status_code == 400        # not failed
    assert client.post("/api/agents/MD-03/fail").json()["status"] == "FAILED"
    assert client.post("/api/agents/MD-03/fail").status_code == 400           # already failed
    assert client.post("/api/agents/MD-03/restore").json()["status"] == "RECOVERING"
    assert client.post("/api/agents/SP-01/move", json={"latitude": 12.97, "longitude": 79.156}).status_code == 400
    assert client.post("/api/agents", json={"agent_type": "MONITOR_DRONE", "agent_id": "MD-01"}).status_code == 400
    assert client.post("/api/agents", json={"agent_type": "ROBOT"}).status_code == 422
    assert client.post("/api/agents/MD-02/sensors", json={"smoke": 5}).status_code == 422
    assert client.post("/api/agents/MD-02/sensors", json={"duration_ticks": 5}).status_code == 400
    ok = client.post("/api/agents/MD-02/sensors", json={"temperature": 33, "duration_ticks": 3})
    assert ok.status_code == 200 and ok.json()["sensor_override"] is True
    moved = client.post("/api/agents/MD-04/move", json={"latitude": 12.968, "longitude": 79.155})
    assert moved.status_code == 200 and moved.json()["destination_label"] == "Manual move"


def test_incident_lifecycle_through_api(client):
    lat, lng = offset(12.9692, 79.1559, 300, 250)
    assert client.post("/api/incidents", json={"type": "FIRE", "latitude": lat + 1, "longitude": lng}).status_code == 400
    assert client.post("/api/incidents", json={"type": "FLOOD", "latitude": lat, "longitude": lng}).status_code == 422
    created = client.post("/api/incidents", json={"type": "FIRE", "latitude": lat, "longitude": lng}).json()
    incident_id = created["id"]
    assert created["status"] == "UNDETECTED"
    client.post("/api/simulation/step", json={"ticks": 25})
    detail = client.get(f"/api/incidents/{incident_id}").json()
    assert detail["status"] in ("CONFIRMED", "RESPONDING")
    assert detail["tasks"] and detail["timeline"] and detail["messages"]
    assert client.get("/api/incidents/INC-NOPE").status_code == 404
    assert client.get("/api/tasks").json()["tasks"]
    net = client.get("/api/network").json()
    assert net["nodes"] and net["links"] and "connected" in net


def test_history_and_analytics_come_from_database(client):
    client.post("/api/simulation/step", json={"ticks": 10})
    history = client.get("/api/history?limit=500").json()["history"]
    categories = {h["category"] for h in history}
    assert {"INCIDENT", "DETECTION", "CONSENSUS", "TASK", "FAILURE"} <= categories
    assert client.get("/api/history?category=BOGUS").status_code == 400
    assert client.get("/api/history/messages?type=INCIDENT_ALERT").json()["messages"]
    assert client.get("/api/history/incidents").json()["incidents"]
    assert client.get("/api/history/failures").json()["failures"]
    assert client.get("/api/history/task-events").json()["events"]
    assert client.get("/api/history/network-events").json()["events"]
    analytics = client.get("/api/analytics").json()
    assert analytics["incidents"]["total"] >= 1
    assert analytics["environment_series"], "telemetry samples should exist"
    assert analytics["messages_by_type"]["INCIDENT_ALERT"] > 0


def test_websocket_ping_and_state(client):
    with client.websocket_connect("/ws") as ws:
        first = ws.receive_json()
        assert first["type"] == "state" and len(first["data"]["agents"]) == 20
        ws.send_text("ping")
        assert ws.receive_text() == "pong"


def test_history_survives_backend_restart(client):
    before = len(client.get("/api/history/incidents").json()["incidents"])
    restarted = SimulationService()                      # new process state, same database
    stored = restarted.stored_incidents()
    assert len(stored) == before
    assert all(i["status"] not in ("DETECTED", "CONFIRMED", "RESPONDING") for i in stored)
    assert restarted.engine.run_id > get_service().engine.run_id - 1
