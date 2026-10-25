"""End-to-end behaviour of the simulation engine (no web server involved)."""

from tests.helpers import CENTER, fire_near_sprinkler, make_engine, run_until
from simulation.geo import haversine_m, offset


def test_deploy_places_twenty_typed_agents_inside_radius(engine):
    assert len(engine.agents) == 20
    types = {a.agent_type for a in engine.agents}
    assert types == {"MONITOR_DRONE", "FIRE_DRONE", "SPRINKLER", "POLLUTION_UNIT", "COOLING_UNIT"}
    positions = {(round(a.lat, 6), round(a.lng, 6)) for a in engine.agents}
    assert len(positions) == 20                      # no two agents on the same spot
    for a in engine.agents:
        assert haversine_m(a.lat, a.lng, *CENTER) <= 1200


def test_monitor_drones_patrol_and_sprinklers_stay_fixed(engine):
    before = {a.agent_id: (a.lat, a.lng) for a in engine.agents}
    for _ in range(10):
        engine.step()
    for a in engine.agents:
        moved = haversine_m(a.lat, a.lng, *before[a.agent_id])
        if a.agent_type == "MONITOR_DRONE":
            assert a.status == "PATROLLING" and moved > 50
        if a.agent_type == "SPRINKLER":
            assert moved == 0


def test_routes_differ_between_drones(engine):
    routes = [tuple(map(tuple, a.patrol_route)) for a in engine.agents if a.agent_type == "MONITOR_DRONE"]
    assert len(set(routes)) == len(routes)


def test_sensor_change_depends_on_distance(engine):
    lat, lng = offset(*CENTER, 300, 250)
    incident = engine.create_incident("FIRE", lat, lng)
    for _ in range(4):
        engine.step()
    near = [a for a in engine.agents if haversine_m(a.lat, a.lng, lat, lng) < 250]
    far = [a for a in engine.agents if haversine_m(a.lat, a.lng, lat, lng) > 1200]
    assert near and far
    assert min(a.readings["temperature"] for a in near) > max(a.readings["temperature"] for a in far) + 5
    assert max(a.readings["smoke"] for a in far) < 0.2
    assert incident.status != "UNDETECTED"   # the agents noticed through their sensors


def test_full_fire_workflow():
    engine = make_engine()
    incident = fire_near_sprinkler(engine)
    assert incident.status == "UNDETECTED"

    assert run_until(engine, lambda: incident.status == "DETECTED", 30)
    assert incident.detectors and incident.coordinator_id in incident.detectors
    alerts = [m for m in engine.comms.recent if m["type"] == "INCIDENT_ALERT"]
    assert alerts, "detector must alert its neighbours"

    assert run_until(engine, lambda: incident.status in ("CONFIRMED", "RESPONDING"), 40)
    cons = incident.consensus
    assert cons["decision"] == "CONFIRMED"
    assert len(cons["supporters"]) >= 2 and cons["confidence"] >= 0.6
    assert incident.confirmed_tick > incident.detected_tick   # evidence exchange takes at least a tick
    assert any(m["type"] == "SENSOR_EVIDENCE" for m in engine.comms.recent)

    response = [engine.tasks[t] for t in incident.task_ids if engine.tasks[t].task_type != "INVESTIGATE"]
    suppression = [t for t in response if t.task_type == "FIRE_SUPPRESSION"]
    assert len(suppression) == 2
    for task in suppression:
        owner = engine.agents_by_id[task.owner_id]
        assert owner.agent_type == "FIRE_DRONE"
        assert task.last_decision and task.last_decision[0]["agent_id"] == owner.agent_id
    assert any(m["type"] == "TASK_PROPOSAL" for m in engine.comms.recent)
    assert any(m["type"] == "TASK_ACCEPTED" for m in engine.comms.recent)

    drone = engine.agents_by_id[suppression[0].owner_id]
    start = haversine_m(drone.lat, drone.lng, incident.lat, incident.lng)
    engine.step(); engine.step()
    assert haversine_m(drone.lat, drone.lng, incident.lat, incident.lng) < start   # really moving toward it

    assert run_until(engine, lambda: incident.status == "RESPONDING", 60)
    peak = incident.severity
    for _ in range(10):
        engine.step()
    assert incident.severity < peak                                  # response lowers severity

    assert run_until(engine, lambda: incident.status == "RESOLVED", 200)
    assert incident.severity <= 3.0
    assert all(engine.tasks[t].status in ("COMPLETED", "CANCELLED") for t in incident.task_ids)
    assert any(m["type"] == "TASK_COMPLETED" for m in engine.comms.recent)
    assert all(a.task_id is None for a in engine.agents)


def test_readings_return_to_normal_after_resolution():
    engine = make_engine()
    incident = fire_near_sprinkler(engine)
    assert run_until(engine, lambda: incident.status == "RESOLVED", 250)
    for _ in range(15):
        engine.step()
    assert all(a.ai_result["status"] == "NORMAL" for a in engine.agents)


def test_pollution_uses_pollution_units():
    engine = make_engine()
    lat, lng = offset(*CENTER, -300, -200)
    incident = engine.create_incident("POLLUTION", lat, lng)
    assert run_until(engine, lambda: incident.status in ("CONFIRMED", "RESPONDING"), 60)
    owners = {engine.tasks[t].owner_id for t in incident.task_ids if engine.tasks[t].task_type == "POLLUTION_CLEANUP"}
    assert owners and all(o.startswith("PU-") for o in owners)
    assert run_until(engine, lambda: incident.status == "RESOLVED", 250)


def test_untreated_fire_grows():
    engine = make_engine()
    for a in engine.agents:          # nobody can sense or respond
        if a.agent_type != "MONITOR_DRONE":
            pass
    lat, lng = offset(*CENTER, 300, 250)
    incident = engine.create_incident("FIRE", lat, lng)
    for a in list(engine.agents):
        engine.fail_agent(a.agent_id)
    start = incident.severity
    for _ in range(20):
        engine.step()
    assert incident.severity > start
    assert incident.status == "UNDETECTED"     # failed agents cannot detect anything
