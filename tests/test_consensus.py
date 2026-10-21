import pytest
from agents.monitoring_agent import MonitoringAgent
from agents.consensus import ConsensusManager


def test_local_consensus_fire():
    a1 = MonitoringAgent("A1", 1, 1, 45.0, 15.0, 0.9, 950.0, 80.0, 20.0)
    a2 = MonitoringAgent("A2", 2, 1, 44.0, 18.0, 0.85, 920.0, 75.0, 22.0)
    a3 = MonitoringAgent("A3", 3, 1, 28.0, 60.0, 0.1, 420.0, 50.0, 55.0)

    a1.add_neighbor(a2)
    a1.add_neighbor(a3)

    res = ConsensusManager.local_consensus(a1, threshold=0.5)

    assert res["consensus"] is True
    assert res["event"] == "FIRE"
    assert res["confidence"] >= 0.6
