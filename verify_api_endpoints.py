import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_all_endpoints():
    results = {}
    
    print("\n--- Testing API Endpoints ---")
    
    # 1. Root
    try:
        r = requests.get(f"{BASE_URL}/")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert r.json()["status"] == "running"
        results["GET /"] = "PASSED"
    except Exception as e:
        results["GET /"] = f"FAILED: {e}"

    # 2. Status
    try:
        r = requests.get(f"{BASE_URL}/api/status")
        assert r.status_code == 200
        data = r.json()
        assert "total_agents" in data and "active_agents" in data
        results["GET /api/status"] = f"PASSED (Agents: {data['active_agents']}/{data['total_agents']})"
    except Exception as e:
        results["GET /api/status"] = f"FAILED: {e}"

    # 3. Agents list
    try:
        r = requests.get(f"{BASE_URL}/api/agents")
        assert r.status_code == 200
        agents = r.json()["agents"]
        assert len(agents) > 0
        results["GET /api/agents"] = f"PASSED ({len(agents)} agents)"
    except Exception as e:
        results["GET /api/agents"] = f"FAILED: {e}"

    # 4. Agent Detail
    try:
        r = requests.get(f"{BASE_URL}/api/agents/A1")
        assert r.status_code == 200
        detail = r.json()
        assert detail["id"] == "A1"
        assert "readings" in detail and "ai_explanation" in detail
        results["GET /api/agents/A1"] = "PASSED"
    except Exception as e:
        results["GET /api/agents/A1"] = f"FAILED: {e}"

    # 5. Create Agent
    created_id = "TEST_A99"
    try:
        payload = {
            "id": created_id,
            "x": 15,
            "y": 15,
            "temperature": 29.5,
            "humidity": 55.0,
            "smoke": 0.08,
            "co2": 410.0,
            "air_quality": 45.0,
            "soil_moisture": 50.0,
            "battery": 100
        }
        r = requests.post(f"{BASE_URL}/api/agents", json=payload)
        assert r.status_code == 200
        res = r.json()
        assert res["success"] is True and res["agent"]["id"] == created_id
        results["POST /api/agents"] = "PASSED"
    except Exception as e:
        results["POST /api/agents"] = f"FAILED: {e}"

    # 6. Update Agent (PATCH)
    try:
        patch_payload = {
            "temperature": 32.0,
            "smoke": 0.15
        }
        r = requests.patch(f"{BASE_URL}/api/agents/{created_id}", json=patch_payload)
        assert r.status_code == 200
        updated = r.json()
        assert updated["readings"]["temperature"] == 32.0
        results[f"PATCH /api/agents/{created_id}"] = "PASSED"
    except Exception as e:
        results[f"PATCH /api/agents/{created_id}"] = f"FAILED: {e}"

    # 7. Move Direction
    try:
        r = requests.post(f"{BASE_URL}/api/agents/{created_id}/move-direction?direction=UP")
        assert r.status_code == 200
        assert r.json()["success"] is True
        results[f"POST /api/agents/{created_id}/move-direction"] = "PASSED"
    except Exception as e:
        results[f"POST /api/agents/{created_id}/move-direction"] = f"FAILED: {e}"

    # 8. Step Patrol
    try:
        r = requests.post(f"{BASE_URL}/api/simulation/patrol-step")
        assert r.status_code == 200
        assert r.json()["success"] is True
        results["POST /api/simulation/patrol-step"] = "PASSED"
    except Exception as e:
        results["POST /api/simulation/patrol-step"] = f"FAILED: {e}"

    # 9. Trigger Agent Analysis
    try:
        r = requests.post(f"{BASE_URL}/api/agents/{created_id}/analyze")
        assert r.status_code == 200
        data = r.json()
        assert "ai_result" in data and "ai_explanation" in data
        results[f"POST /api/agents/{created_id}/analyze"] = "PASSED"
    except Exception as e:
        results[f"POST /api/agents/{created_id}/analyze"] = f"FAILED: {e}"

    # 10. Fail Agent
    try:
        r = requests.post(f"{BASE_URL}/api/agents/{created_id}/fail")
        assert r.status_code == 200
        assert r.json()["agent"]["status"] == "FAILED"
        results[f"POST /api/agents/{created_id}/fail"] = "PASSED"
    except Exception as e:
        results[f"POST /api/agents/{created_id}/fail"] = f"FAILED: {e}"

    # 11. Restore Agent
    try:
        r = requests.post(f"{BASE_URL}/api/agents/{created_id}/restore")
        assert r.status_code == 200
        assert r.json()["agent"]["status"] == "ACTIVE"
        results[f"POST /api/agents/{created_id}/restore"] = "PASSED"
    except Exception as e:
        results[f"POST /api/agents/{created_id}/restore"] = f"FAILED: {e}"

    # 12. Delete Agent
    try:
        r = requests.delete(f"{BASE_URL}/api/agents/{created_id}")
        assert r.status_code == 200
        assert r.json()["success"] is True
        results[f"DELETE /api/agents/{created_id}"] = "PASSED"
    except Exception as e:
        results[f"DELETE /api/agents/{created_id}"] = f"FAILED: {e}"

    # 13. Network
    try:
        r = requests.get(f"{BASE_URL}/api/network")
        assert r.status_code == 200
        net = r.json()
        assert "nodes" in net and "links" in net and "is_connected" in net
        results["GET /api/network"] = f"PASSED ({len(net['nodes'])} nodes, {len(net['links'])} links)"
    except Exception as e:
        results["GET /api/network"] = f"FAILED: {e}"

    # 14. Network Recover
    try:
        r = requests.post(f"{BASE_URL}/api/network/recover")
        assert r.status_code == 200
        assert r.json()["success"] is True
        results["POST /api/network/recover"] = "PASSED"
    except Exception as e:
        results["POST /api/network/recover"] = f"FAILED: {e}"

    # 15. Events Fire
    try:
        r = requests.post(f"{BASE_URL}/api/events/fire", json={"center_x": 10, "center_y": 10, "radius": 3})
        assert r.status_code == 200
        evt = r.json()
        assert evt["event_type"] == "FIRE"
        assert evt["consensus_state"] in ["CONFIRMED", "UNCERTAIN"]
        results["POST /api/events/fire"] = f"PASSED (Consensus: {evt['consensus_state']}, Confidence: {evt['confidence']})"
    except Exception as e:
        results["POST /api/events/fire"] = f"FAILED: {e}"

    # 16. Events Pollution
    try:
        r = requests.post(f"{BASE_URL}/api/events/pollution", json={"center_x": 10, "center_y": 10, "radius": 3})
        assert r.status_code == 200
        evt = r.json()
        assert evt["event_type"] == "POLLUTION"
        results["POST /api/events/pollution"] = "PASSED"
    except Exception as e:
        results["POST /api/events/pollution"] = f"FAILED: {e}"

    # 17. Events Extreme Heat
    try:
        r = requests.post(f"{BASE_URL}/api/events/extreme-heat", json={"center_x": 10, "center_y": 10, "radius": 3})
        assert r.status_code == 200
        evt = r.json()
        assert evt["event_type"] == "EXTREME_HEAT"
        results["POST /api/events/extreme-heat"] = "PASSED"
    except Exception as e:
        results["POST /api/events/extreme-heat"] = f"FAILED: {e}"

    # 18. List Events
    try:
        r = requests.get(f"{BASE_URL}/api/events")
        assert r.status_code == 200
        events = r.json()["events"]
        assert len(events) > 0
        results["GET /api/events"] = f"PASSED ({len(events)} events recorded)"
    except Exception as e:
        results["GET /api/events"] = f"FAILED: {e}"

    # 19. Fail fire agent helper
    try:
        # First trigger fire to ensure fire agent exists
        requests.post(f"{BASE_URL}/api/events/fire")
        r = requests.post(f"{BASE_URL}/api/agents/fail-fire-agent")
        assert r.status_code == 200
        results["POST /api/agents/fail-fire-agent"] = f"PASSED (Failed: {r.json().get('failed_agent')})"
    except Exception as e:
        results["POST /api/agents/fail-fire-agent"] = f"FAILED: {e}"

    # 20. History
    try:
        r = requests.get(f"{BASE_URL}/api/history?category=ALL&limit=50")
        assert r.status_code == 200
        history = r.json()["history"]
        assert len(history) > 0
        results["GET /api/history"] = f"PASSED ({len(history)} logs)"
    except Exception as e:
        results["GET /api/history"] = f"FAILED: {e}"

    # 21. Analytics
    try:
        r = requests.get(f"{BASE_URL}/api/analytics")
        assert r.status_code == 200
        analytics = r.json()
        assert "temperature_trend" in analytics and "active_vs_failed" in analytics
        results["GET /api/analytics"] = "PASSED"
    except Exception as e:
        results["GET /api/analytics"] = f"FAILED: {e}"

    # 22. Simulation Reset
    try:
        r = requests.post(f"{BASE_URL}/api/simulation/reset")
        assert r.status_code == 200
        st = r.json()
        assert st["active_agents"] == 20
        results["POST /api/simulation/reset"] = "PASSED (Reset to 20 agents)"
    except Exception as e:
        results["POST /api/simulation/reset"] = f"FAILED: {e}"

    print("\n--- Verification Summary ---")
    all_passed = True
    for endpoint, res in results.items():
        print(f"[{'PASS' if 'PASSED' in res else 'FAIL'}] {endpoint}: {res}")
        if "FAILED" in res:
            all_passed = False

    return all_passed

if __name__ == "__main__":
    success = test_all_endpoints()
    sys.exit(0 if success else 1)
