import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "total_agents" in data
    assert "active_agents" in data
    assert data["total_agents"] >= 20


def test_api_agents_list_and_detail():
    response = client.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()["agents"]
    assert len(agents) >= 20

    agent_id = agents[0]["id"]
    detail_res = client.get(f"/api/agents/{agent_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == agent_id


def test_api_fire_event_and_recovery():
    # 1. Trigger FIRE event
    fire_res = client.post("/api/events/fire")
    assert fire_res.status_code == 200
    event_data = fire_res.json()
    assert event_data["event_type"] == "FIRE"
    assert event_data["consensus_state"] == "CONFIRMED"

    # 2. Fail an agent
    fail_res = client.post("/api/agents/fail-fire-agent")
    assert fail_res.status_code == 200

    # 3. Recover network
    recover_res = client.post("/api/network/recover")
    assert recover_res.status_code == 200
    assert recover_res.json()["success"] is True

    # 4. Check history
    history_res = client.get("/api/history")
    assert history_res.status_code == 200
    assert len(history_res.json()["history"]) > 0
