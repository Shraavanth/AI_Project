import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_persistence_after_restart():
    print("\n--- Verifying Database Persistence After Backend Restart ---")
    
    # 1. Check /api/status
    r_status = requests.get(f"{BASE_URL}/api/status")
    assert r_status.status_code == 200
    status = r_status.json()
    print(f"Status after restart: Total={status['total_agents']}, Active={status['active_agents']}, Failed={status['failed_agents']}")
    assert status["failed_agents"] >= 1, f"Expected at least 1 failed agent (A6), got {status['failed_agents']}"
    
    # 2. Check Agent A6 state
    r_a6 = requests.get(f"{BASE_URL}/api/agents/A6")
    assert r_a6.status_code == 200
    a6 = r_a6.json()
    print(f"Agent A6 state after restart: status={a6['status']}, battery={a6['battery']}")
    assert a6["status"] == "FAILED", f"Expected A6 to remain FAILED across restart, got {a6['status']}"
    
    # 3. Check /api/events persistence
    r_events = requests.get(f"{BASE_URL}/api/events")
    assert r_events.status_code == 200
    events = r_events.json()["events"]
    print(f"Recorded events in DB after restart: {len(events)}")
    assert len(events) > 0, "Expected events to persist across restart"
    
    # 4. Check last_event
    print(f"Status last_event after restart: {status.get('last_event')}")
    assert status.get("last_event") is not None, "last_event should be restored from database"
    assert status["last_event"]["event_type"] == "FIRE"
    
    # 5. Check /api/history audit logs persistence
    r_history = requests.get(f"{BASE_URL}/api/history?limit=10")
    assert r_history.status_code == 200
    logs = r_history.json()["history"]
    print(f"Audit logs in DB after restart: {len(logs)}")
    assert len(logs) > 0, "Audit logs must persist across backend restart"
    
    # Restore A6 back to clean state
    requests.post(f"{BASE_URL}/api/agents/A6/restore")
    print("[PASS] Full backend persistence after restart verified successfully.")
    return True

if __name__ == "__main__":
    success = test_persistence_after_restart()
    sys.exit(0 if success else 1)
