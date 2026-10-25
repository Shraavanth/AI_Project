import sys
import os

from agents.monitoring_agent import MonitoringAgent
from agents.consensus import ConsensusManager

def test_agent_message_exchange_and_decisions():
    print("\n--- Verifying Agent Message Exchange & Local Decisions ---")
    
    # 1. Create two agents in proximity
    a1 = MonitoringAgent("TEST_A1", 10, 10, temperature=28.0, humidity=60.0, smoke=0.10, co2=420.0, air_quality=50.0, soil_moisture=55.0)
    a2 = MonitoringAgent("TEST_A2", 11, 10, temperature=28.0, humidity=60.0, smoke=0.10, co2=420.0, air_quality=50.0, soil_moisture=55.0)
    
    # Link them as peers
    a1.add_neighbor(a2)
    a2.add_neighbor(a1)
    
    # Both initially analyze baseline
    res1 = a1.analyze_environment()
    res2 = a2.analyze_environment()
    print(f"Agent A1 Baseline Decision: status={res1['status']}, event={res1['event']}")
    assert res1["status"] == "NORMAL"
    assert res2["status"] == "NORMAL"
    
    # Verify no alerts broadcast when normal
    a1.broadcast_alert()
    assert len(a2.messages) == 0, "Normal agent should not broadcast alerts"
    
    # 2. Induce Fire condition on Agent A1
    a1.temperature = 48.0
    a1.smoke = 0.85
    a1.humidity = 18.0
    
    # Agent A1 performs local AI inference
    fire_decision = a1.analyze_environment()
    print(f"Agent A1 Post-Hazard Local Decision: status={fire_decision['status']}, event={fire_decision['event']}, score={fire_decision['score']}")
    assert fire_decision["status"] == "ANOMALY"
    assert fire_decision["event"] == "FIRE"
    
    # 3. Agent A1 broadcasts alert to its active peers
    a1.broadcast_alert()
    print(f"Messages received by Agent A2: {len(a2.messages)}")
    assert len(a2.messages) == 1, "Agent A2 should have received peer alert"
    received = a2.messages[0]
    print(f"Message payload: {received}")
    assert received["sender"] == "TEST_A1"
    assert received["message"]["type"] == "ENVIRONMENTAL_ALERT"
    assert received["message"]["event"] == "FIRE"
    
    # 4. Local neighbor consensus evaluation
    # A1 reports FIRE, A2 reports NORMAL
    local_consensus = ConsensusManager.local_consensus(a1, threshold=0.5)
    print(f"Local Consensus from A1 perspective: {local_consensus}")
    assert local_consensus["event"] in ["FIRE", "UNCERTAIN"]
    
    print("[PASS] Python agents successfully exchanged messages and made autonomous local monitoring decisions.")
    return True

if __name__ == "__main__":
    success = test_agent_message_exchange_and_decisions()
    sys.exit(0 if success else 1)
