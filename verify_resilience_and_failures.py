import requests
import asyncio
import websockets
import sys

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"

def test_api_failure_modes():
    print("\n--- Verifying API Failure Modes & Error Handling ---")
    
    # 1. 404 on nonexistent agent
    r = requests.get(f"{BASE_URL}/api/agents/NONEXISTENT_999")
    print(f"Nonexistent agent response: status={r.status_code}, detail={r.json().get('detail')}")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    
    # 2. 400 on duplicate agent creation
    r = requests.post(f"{BASE_URL}/api/agents", json={"id": "A1", "x": 5, "y": 5})
    print(f"Duplicate agent creation response: status={r.status_code}, detail={r.json().get('detail')}")
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    
    # 3. 400 on restoring an already active agent
    r = requests.post(f"{BASE_URL}/api/agents/A1/restore")
    print(f"Restore active agent response: status={r.status_code}, detail={r.json().get('detail')}")
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    
    # 4. Fail agent, then 400 on failing again
    requests.post(f"{BASE_URL}/api/agents/A1/fail")
    r = requests.post(f"{BASE_URL}/api/agents/A1/fail")
    print(f"Fail already failed agent response: status={r.status_code}, detail={r.json().get('detail')}")
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    
    # Restore A1
    requests.post(f"{BASE_URL}/api/agents/A1/restore")
    
    # 5. Invalid input types on schema validation
    r = requests.post(f"{BASE_URL}/api/agents", json={"id": "BAD_AGENT", "battery": "NOT_AN_INT"})
    print(f"Invalid schema validation response: status={r.status_code}")
    assert r.status_code == 422, f"Expected 422 Unprocessable Entity, got {r.status_code}"
    
    print("[PASS] API error responses and validation status codes verified.")
    return True

async def test_websocket_lifecycle():
    print("\n--- Verifying WebSocket Lifecycle & Clean Disconnection ---")
    async with websockets.connect(WS_URL) as ws:
        print("Connected to WebSocket at /ws")
        # Send heartbeat ping
        await ws.send("ping")
        resp = await ws.recv()
        print(f"Received heartbeat response: {resp}")
        assert resp == "pong", f"Expected pong, got {resp}"
        
        # Abrupt close / disconnection test
        print("Closing WebSocket connection to test clean server-side disconnect...")
        await ws.close()
    
    # Verify server is still completely responsive after disconnection
    r = requests.get(f"{BASE_URL}/api/status")
    assert r.status_code == 200
    print("[PASS] WebSocket connection, heartbeat, and clean disconnection verified.")
    return True

if __name__ == "__main__":
    api_ok = test_api_failure_modes()
    ws_ok = asyncio.run(test_websocket_lifecycle())
    if api_ok and ws_ok:
        print("\n[ALL RESILIENCE CHECKS PASSED]")
        sys.exit(0)
    sys.exit(1)
