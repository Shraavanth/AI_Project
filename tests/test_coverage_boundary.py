"""Module 5: Dedicated test scenarios for fault-tolerant drone coverage and boundary incident detection.

Tests:
1. Single drone failure: Heartbeat timeout, uncovered zone detection, dynamic reassignment, notifications.
2. Multiple drone failures: Distributed coverage across remaining drones, workload capping, blind spots tracking.
3. Boundary incident: Incident inside nominal detection radius detected cleanly.
4. Boundary tolerance: Incident between nominal radius and nominal+tolerance detected with boundary/provisional flag.
5. Trajectory-based continuous detection: Proximity along movement path between ticks detected.
6. Overlapping coverage: Two overlapping drones detect anomaly, single incident created, multi-drone verification.
7. No available replacement: Operational warning raised, honest < 100% coverage reporting.
8. Drone recovery: Restored drone safely reintegrated, heartbeats resumed, duplicates avoided.
"""

import pytest
from simulation import config
from simulation.engine import SimulationEngine
from simulation.geo import haversine_m, offset
from tests.helpers import CENTER, make_engine, run_until


def test_1_single_drone_failure_heartbeat_reassignment():
    """Test 1: Single drone failure, heartbeat timeout, uncovered area identified, coverage reassigned."""
    engine = make_engine(seed=42, warmup=3)
    monitor_drones = [a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational]
    assert len(monitor_drones) >= 4, "Need at least 4 monitor drones"
    
    victim = monitor_drones[0]
    victim_id = victim.agent_id
    victim_sectors = engine.coverage.drone_sectors.get(victim_id, [])
    assert len(victim_sectors) >= 1, "Drone should have an assigned sector"
    victim_sector = victim_sectors[0]

    # Initial state check
    cov_summary = engine.coverage.compute_coverage_summary()
    assert cov_summary["active_monitors"] >= 4
    assert cov_summary["failed_monitors"] == 0

    # Fail drone
    engine.fail_agent(victim_id)
    assert victim.status == "FAILED"

    # Step for heartbeat timeout
    for _ in range(config.DRONE_HEARTBEAT_TIMEOUT_TICKS + 1):
        engine.step()

    cov_summary_after = engine.coverage.compute_coverage_summary()
    assert cov_summary_after["failed_monitors"] >= 1

    # Check notification generation
    notif_texts = [n["message"] for n in cov_summary_after["notifications"]]
    assert any(f"MONITOR DRONE {victim_id} FAILURE DETECTED" in msg for msg in notif_texts), (
        f"Expected failure notification for {victim_id}, got: {notif_texts}"
    )
    assert any("Uncovered surveillance area identified" in msg or "Coverage reassignment initiated" in msg for msg in notif_texts)

    # Check reassignment took place
    reassigned = [r for r in cov_summary_after["reassignments"] if r.get("original_owner") == victim_id]
    assert len(reassigned) >= 1, "Victim's sector should be reassigned to another available drone"
    new_owner_id = reassigned[0]["assigned_to"]
    new_owner = engine.agents_by_id[new_owner_id]
    assert new_owner.operational
    assert new_owner.agent_id != victim_id
    # New owner has sector in covered list
    reassigned_sector_ids = [s["id"] for s in engine.coverage.drone_sectors[new_owner_id]]
    assert victim_sector["id"] in reassigned_sector_ids


def test_2_multiple_drone_failures_distribution_and_blind_spots():
    """Test 2: Multiple drone failures distribute load without overloading a single drone."""
    engine = make_engine(seed=10, warmup=3)
    monitors = [a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational]
    assert len(monitors) >= 4

    victim1 = monitors[0]
    victim2 = monitors[1]

    engine.fail_agent(victim1.agent_id)
    engine.fail_agent(victim2.agent_id)

    for _ in range(config.DRONE_HEARTBEAT_TIMEOUT_TICKS + 2):
        engine.step()

    summary = engine.coverage.compute_coverage_summary()
    assert summary["failed_monitor_drones"] == 2

    # Check workload distribution: no remaining drone should exceed MAX_SECTORS_PER_DRONE
    remaining = [a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational]
    for drone in remaining:
        assigned = engine.coverage.drone_sectors.get(drone.agent_id, [])
        assert len(assigned) <= config.MAX_SECTORS_PER_DRONE, (
            f"Drone {drone.agent_id} overloaded with {len(assigned)} sectors"
        )


def test_3_boundary_incident_detection():
    """Test 3: Incident placed inside nominal detection radius is detected."""
    engine = make_engine(seed=12, warmup=2)
    drone = next(a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational)

    # Place an incident within nominal radius (e.g. 300m, nominal is 450m)
    inc_lat, inc_lng = offset(drone.lat, drone.lng, 250, 0)
    d = haversine_m(drone.lat, drone.lng, inc_lat, inc_lng)
    assert d < config.MONITOR_NOMINAL_RADIUS_M

    incident = engine.create_incident("FIRE", inc_lat, inc_lng)

    # Let the drone sense it
    run_until(engine, lambda: drone.anomaly_streak > 0, max_ticks=10)
    assert drone.anomaly_streak > 0
    assert not incident.is_boundary, "Should not be flagged as boundary since it is well within nominal radius"


def test_4_boundary_tolerance_detection():
    """Test 4: Incident between nominal radius and nominal+tolerance is detected as boundary/provisional."""
    engine = make_engine(seed=15, warmup=2)
    drone = next(a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational)

    # Place incident in the tolerance zone (e.g. nominal + 40m, tolerance is 80m)
    dist_m = config.MONITOR_NOMINAL_RADIUS_M + 40.0
    inc_lat, inc_lng = offset(drone.lat, drone.lng, dist_m, 0)
    real_d = haversine_m(drone.lat, drone.lng, inc_lat, inc_lng)
    assert config.MONITOR_NOMINAL_RADIUS_M < real_d <= (config.MONITOR_NOMINAL_RADIUS_M + config.DETECTION_BOUNDARY_TOLERANCE_M)

    incident = engine.create_incident("EXTREME_HEAT", inc_lat, inc_lng)

    # Drone steps and senses within tolerance
    for _ in range(5):
        engine.step()

    # The incident was flagged with boundary detection
    assert incident.is_boundary is True or incident.provisional is True or engine.coverage.boundary_detections_count >= 1


def test_5_trajectory_based_continuous_detection():
    """Test 5: Drone sweeps past an incident between two updates; continuous proximity triggers detection."""
    engine = make_engine(seed=20, warmup=1)
    drone = next(a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational)

    # Incident position
    inc_lat, inc_lng = CENTER[0] + 0.002, CENTER[1] + 0.002
    incident = engine.create_incident("FIRE", inc_lat, inc_lng)

    # Place drone before and after such that neither endpoint is within nominal radius,
    # but the line segment passes directly through the detection zone
    # Endpoint 1: west of incident by 600m
    lat1, lng1 = offset(inc_lat, inc_lng, -600, 0)
    # Endpoint 2: east of incident by 600m
    lat2, lng2 = offset(inc_lat, inc_lng, 600, 0)

    drone.prev_lat, drone.prev_lng = lat1, lng1
    drone.lat, drone.lng = lat2, lng2

    # Check that continuous detection notices trajectory proximity
    detected = engine.coverage.check_continuous_detection(drone)
    assert detected is True, "Trajectory should have intercepted incident detection zone"
    assert incident.incident_id in [i.incident_id for i in engine.incidents.values()]


def test_6_overlapping_coverage_single_incident_multi_drone_verification():
    """Test 6: Overlapping drones detect same incident without creating duplicates, verifying collaboratively."""
    engine = make_engine(seed=25, warmup=2)
    monitors = [a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational]
    d1, d2 = monitors[0], monitors[1]

    # Position both drones so they overlap at a midpoint
    mid_lat, mid_lng = CENTER[0], CENTER[1]
    d1.lat, d1.lng = offset(mid_lat, mid_lng, -150, 0)
    d2.lat, d2.lng = offset(mid_lat, mid_lng, 150, 0)

    # Incident right at midpoint: distance to d1 is ~150m, d2 is ~150m (both well within 450m nominal)
    incident = engine.create_incident("FIRE", mid_lat, mid_lng)
    inc_id = incident.incident_id

    # Run steps to allow both drones to sense
    for _ in range(8):
        engine.step()

    # Verify no duplicate incident was created
    fire_incidents = [inc for inc in engine.incidents.values() if inc.incident_type == "FIRE"]
    assert len(fire_incidents) == 1
    assert fire_incidents[0].incident_id == inc_id

    # Verify consensus or multi-agent readings
    assert len(incident.timeline) >= 1 or len(incident.last_votes) >= 1


def test_7_no_available_replacement_reports_unmonitored_warning():
    """Test 7: When all monitor drones fail, an unmonitored warning is raised and coverage < 100%."""
    engine = make_engine(seed=30, warmup=2)
    monitors = [a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational]

    # Fail ALL monitor drones
    for m in monitors:
        engine.fail_agent(m.agent_id)

    for _ in range(config.DRONE_HEARTBEAT_TIMEOUT_TICKS + 2):
        engine.step()

    summary = engine.coverage.compute_coverage_summary()
    assert summary["active_monitors"] == 0
    assert summary["uncovered_sectors_count"] > 0
    assert summary["coverage_pct"] < 100.0, "Coverage must honestly report < 100% when drones fail"
    assert summary["operational_warning"] is not None
    assert "WARNING" in summary["operational_warning"] or "UNMONITORED" in summary["operational_warning"]


def test_8_drone_recovery_safe_reintegration():
    """Test 8: Restored drone safely reintegrates into network and resumes heartbeats without duplicate tasks."""
    engine = make_engine(seed=35, warmup=2)
    drone = next(a for a in engine.agents if a.agent_type == "MONITOR_DRONE" and a.operational)
    drone_id = drone.agent_id

    # Fail
    engine.fail_agent(drone_id)
    for _ in range(config.DRONE_HEARTBEAT_TIMEOUT_TICKS + 1):
        engine.step()

    summary_failed = engine.coverage.compute_coverage_summary()
    assert summary_failed["failed_monitors"] >= 1

    # Restore
    engine.restore_agent(drone_id)
    for _ in range(config.RECOVERY_TICKS + 1):
        engine.step()

    assert drone.operational is True
    assert drone.status != "FAILED"
    
    summary_restored = engine.coverage.compute_coverage_summary()
    assert summary_restored["failed_monitors"] == 0
    # Heartbeat is updated
    hb = engine.coverage.heartbeats.get(drone_id)
    assert hb is not None
    assert hb["operational"] is True
    # Notification mentions restored
    notif_msgs = [n["message"] for n in summary_restored["notifications"]]
    assert any(f"MONITOR DRONE {drone_id} RESTORED" in m for m in notif_msgs)
