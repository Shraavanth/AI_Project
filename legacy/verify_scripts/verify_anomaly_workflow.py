import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_full_anomaly_lifecycle():
    print("\n--- Verifying End-to-End Environmental Anomaly Lifecycle ---")
    
    # 1. Reset simulation to clean baseline
    print("Resetting simulation...")
    r_reset = requests.post(f"{BASE_URL}/api/simulation/reset")
    assert r_reset.status_code == 200
    status_before = r_reset.json()
    assert status_before["anomalies"] == 0, f"Expected 0 anomalies, got {status_before['anomalies']}"
    print("Baseline verified: 0 anomalies.")
    
    # 2. Trigger reproducible FIRE anomaly at coordinates (10, 10) with radius 3
    print("Triggering FIRE anomaly at center (10, 10) with radius 3...")
    trigger_payload = {
        "center_x": 10,
        "center_y": 10,
        "radius": 3
    }
    r_fire = requests.post(f"{BASE_URL}/api/events/fire", json=trigger_payload)
    assert r_fire.status_code == 200, f"Trigger failed: {r_fire.text}"
    event_data = r_fire.json()
    
    event_id = event_data["event_id"]
    event_type = event_data["event_type"]
    consensus = event_data["consensus_state"]
    confidence = event_data["confidence"]
    affected_agents = event_data["affected_agents"]
    
    print(f"Hazard Triggered: {event_id} ({event_type})")
    print(f"Affected Agents in Zone: {affected_agents}")
    print(f"Decentralized Consensus: {consensus} (Confidence: {confidence:.2f})")
    
    assert event_type == "FIRE"
    assert len(affected_agents) > 0
    assert consensus in ["CONFIRMED", "UNCERTAIN"]
    
    # 3. Verify affected agents' local AI inference state
    print("Verifying detecting agents' AI state and readings...")
    r_agents = requests.get(f"{BASE_URL}/api/agents")
    agents = r_agents.json()["agents"]
    
    detected_count = 0
    for agent_id in affected_agents:
        agent = next((a for a in agents if a["id"] == agent_id), None)
        assert agent is not None, f"Agent {agent_id} not found"
        print(f"- {agent['id']} at {agent['position']}: Temp={agent['readings']['temperature']}°C, Smoke={agent['readings']['smoke']}, AI={agent['ai_result']['status']} ({agent['ai_result']['event']})")
        if agent["ai_result"] and agent["ai_result"]["event"] == "FIRE":
            detected_count += 1
            assert agent["ai_explanation"]["temperature_level"] in ["HIGH", "VERY HIGH"]
            assert agent["ai_explanation"]["smoke_level"] in ["HIGH", "VERY HIGH"]
    
    assert detected_count > 0, "At least one agent must detect FIRE"
    print(f"Verified: {detected_count} agents independently classified FIRE anomaly.")
    
    # 4. Verify Incident Record persisted in database
    print("Verifying database persistence in /api/events...")
    r_events = requests.get(f"{BASE_URL}/api/events")
    all_events = r_events.json()["events"]
    persisted_event = next((e for e in all_events if e["event_id"] == event_id), None)
    assert persisted_event is not None, f"Event {event_id} was not persisted in database"
    assert persisted_event["event_type"] == "FIRE"
    print(f"Verified incident {event_id} persisted in DB.")
    
    # 5. Verify Audit Log entry created in database
    print("Verifying audit log entry in /api/history...")
    r_history = requests.get(f"{BASE_URL}/api/history?category=EVENT&limit=10")
    history_logs = r_history.json()["history"]
    matching_log = next((l for l in history_logs if event_id in l.get("details", {}).get("event_id", "") or "FIRE" in l["title"]), None)
    assert matching_log is not None, "Audit trail log not found for FIRE event"
    print(f"Verified audit log: [{matching_log['category']}] {matching_log['title']} - {matching_log['message']}")
    
    print("[PASS] Full detection, neighbor-validation, incident-creation, and history-persistence workflow verified successfully.")
    return True

if __name__ == "__main__":
    success = test_full_anomaly_lifecycle()
    sys.exit(0 if success else 1)
