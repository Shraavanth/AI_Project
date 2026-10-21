import pytest
from agents.monitoring_agent import MonitoringAgent
from agents.communication import CommunicationManager


def test_agent_creation_and_metrics():
    agent = MonitoringAgent(
        agent_id="A1",
        x=5,
        y=5,
        temperature=28.0,
        humidity=60.0,
        smoke=0.1,
        co2=420.0,
        air_quality=50.0,
        soil_moisture=55.0,
        battery=95
    )

    info = agent.get_info()
    assert info["id"] == "A1"
    assert info["position"] == (5, 5)
    assert info["status"] == "ACTIVE"
    assert info["health"] > 80
    assert "ai_explanation" in info


def test_agent_communication():
    a1 = MonitoringAgent("A1", 1, 1, 45.0, 15.0, 0.9, 950.0, 80.0, 20.0)
    a2 = MonitoringAgent("A2", 2, 1, 28.0, 60.0, 0.1, 420.0, 50.0, 55.0)

    a1.add_neighbor(a2)
    a2.add_neighbor(a1)

    # a1 is anomalous, should send alert to a2
    a1.broadcast_alert()

    assert len(a2.messages) == 1
    assert a2.messages[0]["sender"] == "A1"
    assert a2.messages[0]["message"]["event"] == "FIRE"
