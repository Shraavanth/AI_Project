"""Agent failure, failure detection, task reassignment and honest outcomes."""

import pytest

from tests.helpers import fire_near_sprinkler, make_engine, run_until
from simulation import config


def _engine_with_responding_drone():
    engine = make_engine()
    incident = fire_near_sprinkler(engine)

    def drone_on_site():
        return any(engine.tasks[t].task_type == "FIRE_SUPPRESSION" and engine.tasks[t].status == "IN_PROGRESS"
                   for t in incident.task_ids)
    assert run_until(engine, drone_on_site, 80)
    task = next(engine.tasks[t] for t in incident.task_ids
                if engine.tasks[t].task_type == "FIRE_SUPPRESSION" and engine.tasks[t].status == "IN_PROGRESS")
    return engine, incident, task


def test_failed_responder_is_replaced_by_another_capable_agent():
    engine, incident, task = _engine_with_responding_drone()
    victim = engine.agents_by_id[task.owner_id]
    position = (victim.lat, victim.lng)
    links_before = engine.network.graph.number_of_edges()

    engine.fail_agent(victim.agent_id)

    # Immediate effects
    assert victim.status == "FAILED"
    assert task.status == "INTERRUPTED"
    assert victim.agent_id not in engine.network.graph
    assert victim.neighbors == []
    assert engine.network.graph.number_of_edges() < links_before
    event = engine.network_events[0]
    assert event["trigger"] == "FAILURE" and event["links_removed"]

    # Not reassigned instantly: neighbours must first notice the missing heartbeat
    engine.step()
    assert task.owner_id == victim.agent_id
    sent_before = victim.messages_sent

    assert run_until(engine, lambda: task.owner_id not in (None, victim.agent_id), config.HEARTBEAT_TIMEOUT_TICKS + 2)
    new_owner = engine.agents_by_id[task.owner_id]
    assert new_owner.agent_type == "FIRE_DRONE" and new_owner.operational
    assert task.reassign_count == 1
    assert [o["agent_id"] for o in task.owners] == [victim.agent_id, new_owner.agent_id]
    assert task.owners[0]["end"] == "INTERRUPTED"
    assert victim.task_id is None and new_owner.task_id == task.task_id

    failure = next(iter(engine.failures.values()))
    assert failure["detected_tick"] - failure["failed_tick"] == config.HEARTBEAT_TIMEOUT_TICKS
    assert failure["detection_method"] in ("PEER_HEARTBEAT", "TASK_OWNER_TIMEOUT")
    assert failure["reassigned_to"] == new_owner.agent_id
    types = {m["type"] for m in engine.comms.recent}
    assert {"FAILURE_ALERT", "TASK_REASSIGNED"} <= types

    # The failed agent stays put and silent; the replacement does the work
    for _ in range(10):
        engine.step()
    assert (victim.lat, victim.lng) == position
    assert victim.messages_sent == sent_before
    assert run_until(engine, lambda: incident.status == "RESOLVED", 250)
    assert task.status == "COMPLETED" and task.owner_id == new_owner.agent_id


def test_coordinator_failure_triggers_reelection():
    engine, incident, _ = _engine_with_responding_drone()
    old = incident.coordinator_id
    engine.fail_agent(old)
    engine.step()
    assert incident.coordinator_id != old
    assert engine.agents_by_id[incident.coordinator_id].operational
    assert any(m["type"] == "COORDINATOR_CHANGE" for m in engine.comms.recent)


def test_no_replacement_means_needs_intervention_and_fire_does_not_vanish():
    engine, incident, _ = _engine_with_responding_drone()
    for agent in list(engine.agents):
        if agent.agent_type in ("FIRE_DRONE", "SPRINKLER") and agent.status != "FAILED":
            engine.fail_agent(agent.agent_id)
    severity = incident.severity
    assert run_until(engine, lambda: incident.status == "NEEDS_INTERVENTION", 40)
    assert incident.severity > severity                      # untreated fire keeps growing
    unassigned = [engine.tasks[t] for t in incident.task_ids if engine.tasks[t].status == "UNASSIGNED"]
    assert unassigned and all(t.owner_id is None for t in unassigned)

    # A restored fire drone picks the work up again
    drone = next(a for a in engine.agents if a.agent_type == "FIRE_DRONE")
    engine.restore_agent(drone.agent_id)
    assert drone.status == "RECOVERING"
    assert run_until(engine, lambda: drone.task_id is not None, config.RECOVERY_TICKS + 3)
    assert run_until(engine, lambda: incident.status == "RESPONDING", 80)


def test_restore_rejoins_network():
    engine = make_engine()
    agent = engine.agents_by_id["MD-01"]
    engine.fail_agent("MD-01")
    engine.step()
    engine.restore_agent("MD-01")
    assert agent.status == "RECOVERING" and agent.battery == 100
    run_until(engine, lambda: agent.status != "RECOVERING", config.RECOVERY_TICKS + 1)
    assert agent.operational and "MD-01" in engine.network.graph
    assert engine.network_events[0]["trigger"] == "RESTORE"


def test_battery_depletion_fails_agent():
    engine = make_engine()
    drone = engine.agents_by_id["MD-01"]
    drone.battery = 0.01
    drone.charge_mode = False
    engine.step()          # moves a little, battery reaches 0
    engine.step()          # empty battery is noticed: the drone fails
    assert drone.status == "FAILED" and drone.failure_reason == "BATTERY_DEPLETED"


def test_invalid_operations():
    engine = make_engine()
    with pytest.raises(KeyError):
        engine.fail_agent("NOPE")
    engine.fail_agent("MD-02")
    with pytest.raises(ValueError):
        engine.fail_agent("MD-02")
    with pytest.raises(ValueError):
        engine.restore_agent("MD-03")       # not failed
    with pytest.raises(ValueError):
        engine.move_agent("SP-01", engine.site["lat"], engine.site["lng"])   # fixed sprinkler
    with pytest.raises(ValueError):
        engine.create_incident("FIRE", engine.site["lat"] + 1, engine.site["lng"])  # outside area
    with pytest.raises(ValueError):
        engine.create_incident("FLOOD", engine.site["lat"], engine.site["lng"])
    with pytest.raises(ValueError):
        engine.add_agent("MONITOR_DRONE", agent_id="MD-01")   # duplicate id


def test_two_failed_monitor_drones_area_still_monitored_and_resolved():
    engine = make_engine()
    # 1. Fail two monitoring drones in an area
    md1 = engine.agents_by_id["MD-01"]
    target_lat, target_lng = md1.lat, md1.lng
    engine.fail_agent("MD-01")
    engine.fail_agent("MD-02")
    engine.step()

    # The 6 surviving monitoring drones dynamically expand their patrol routes
    active_monitors = [a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational]
    assert len(active_monitors) == 6
    for m in active_monitors:
        assert len(m.patrol_route) == 6

    # 2. Place an incident in the sector of the failed drones
    incident = engine.create_incident("FIRE", target_lat, target_lng, radius_m=350.0, severity=50.0)

    # 3. Remaining fleet coordinates, investigates, confirms and responds
    assert run_until(engine, lambda: incident.status in ("CONFIRMED", "RESPONDING", "RESOLVED"), 120)

    # 4. Response drones fly to the area and begin fire suppression
    def responders_active():
        return any(engine.tasks[t].task_type == "FIRE_SUPPRESSION" and engine.tasks[t].status in ("IN_PROGRESS", "COMPLETED")
                   for t in incident.task_ids)
    assert run_until(engine, responders_active, 100)
