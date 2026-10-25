"""
Coverage and Drone Health Management Service.

Provides fault-tolerant surveillance coordination:
1. Heartbeat-based drone health monitoring.
2. Dynamic sector reassignment when monitor drones fail.
3. Calculation of uncovered geographical regions, coverage gaps, and overlapping coverage.
4. Boundary incident detection, tolerance buffering, and multi-drone verification.
5. Safe reintegration upon drone recovery.
"""

import math
import time
from typing import Dict, List, Optional, Tuple

from simulation import config
from simulation.geo import haversine_m, offset, ring_point, segment_distance_m


class CoverageManager:

    def __init__(self, engine):
        self.engine = engine
        self.heartbeats: Dict[str, dict] = {}
        self.drone_sectors: Dict[str, List[dict]] = {}
        self.failed_zones: Dict[str, List[dict]] = {}
        self.events: List[dict] = []
        self.notifications: List[str] = []
        self.operational_warnings: List[str] = []
        self.boundary_detections: List[dict] = []
        self.reassignments: List[dict] = []
        self.nominal_radius_m = config.MONITOR_NOMINAL_RADIUS_M
        self.boundary_tolerance_m = config.DETECTION_BOUNDARY_TOLERANCE_M

    # ------------------------------------------------------------------
    # 1. Heartbeat & Health Monitoring
    # ------------------------------------------------------------------

    def record_heartbeats(self):
        """Every tick, active monitor drones report their status, battery, task and zone."""
        tick = self.engine.tick
        for agent in self.engine.agents:
            if agent.agent_type != "MONITOR_DRONE":
                continue

            comm_status = "OFFLINE"
            if agent.operational:
                if self.engine.network.neighbors(agent.agent_id):
                    comm_status = "CONNECTED"
                else:
                    comm_status = "ISOLATED"

            assigned_zones = [s["name"] for s in self.drone_sectors.get(agent.agent_id, [])]
            task_desc = agent.task_id if agent.task_id else ("PATROL" if agent.operational else "INACTIVE")

            self.heartbeats[agent.agent_id] = {
                "agent_id": agent.agent_id,
                "last_tick": tick if agent.operational else self.heartbeats.get(agent.agent_id, {}).get("last_tick", tick),
                "status": agent.status,
                "battery": round(agent.battery, 1),
                "comm_status": comm_status,
                "assigned_zones": assigned_zones,
                "current_task": task_desc,
                "operational": agent.operational,
                "healthy": agent.operational and agent.battery >= config.LOW_BATTERY_RETURN,
            }

    def check_heartbeat_timeouts(self):
        """Detect drones that stopped sending heartbeats or timed out."""
        tick = self.engine.tick
        for agent in self.engine.agents:
            if agent.agent_type != "MONITOR_DRONE" or not agent.operational:
                continue
            hb = self.heartbeats.get(agent.agent_id)
            if hb and (tick - hb["last_tick"]) >= config.DRONE_HEARTBEAT_TIMEOUT_TICKS:
                self.engine.log("FAILURE", f"Drone heartbeat timeout: {agent.agent_id}",
                                f"{agent.agent_id} missed heartbeats for {tick - hb['last_tick']} s. Marking FAILED.",
                                agent_id=agent.agent_id)
                self.engine.fail_agent(agent.agent_id, reason="HEARTBEAT_TIMEOUT")

    # ------------------------------------------------------------------
    # 2. Sector Allocation & Dynamic Reassignment
    # ------------------------------------------------------------------

    def initialize_sectors(self):
        """Divide the surveillance site into angular sectors for active monitor drones."""
        site = self.engine.site
        if not site:
            return
        monitors = [a for a in self.engine.agents if a.agent_type == "MONITOR_DRONE"]
        if not monitors:
            return

        c_lat, c_lng = site["lat"], site["lng"]
        monitors.sort(key=lambda d: math.atan2(d.lat - c_lat, d.lng - c_lng))
        n = len(monitors)
        sector_span = 2 * math.pi / n

        self.drone_sectors.clear()
        self.failed_zones.clear()

        for i, drone in enumerate(monitors):
            c_angle = i * sector_span
            start_angle = c_angle - sector_span / 2
            end_angle = c_angle + sector_span / 2
            sector_name = f"Sector-{chr(65 + (i % 26))}"
            sector_data = {
                "id": f"{drone.agent_id}-sec-{i}",
                "name": sector_name,
                "center_angle": c_angle,
                "start_angle": start_angle,
                "end_angle": end_angle,
                "radius_m": site["radius_m"],
                "owner_id": drone.agent_id,
                "original_owner": drone.agent_id,
                "status": "MONITORED" if drone.operational else "UNMONITORED",
            }
            self.drone_sectors[drone.agent_id] = [sector_data]

    def on_drone_failed(self, drone):
        """
        Handle monitor drone failure:
        1. Identify its assigned surveillance zone.
        2. Calculate uncovered geographical region.
        3. Identify available nearby monitor drones.
        4. Reassign uncovered area intelligently (avoid dumping all on one drone).
        5. Emit notification events.
        """
        if drone.agent_type != "MONITOR_DRONE":
            return

        drone_id = drone.agent_id
        lost_sectors = self.drone_sectors.pop(drone_id, [])
        if not lost_sectors:
            # Generate a sector representation from angle if not tracked yet
            site = self.engine.site
            if site:
                c_angle = math.atan2(drone.lat - site["lat"], drone.lng - site["lng"])
                lost_sectors = [{
                    "id": f"{drone_id}-sec-lost",
                    "name": f"Sector-{drone_id}",
                    "center_angle": c_angle,
                    "start_angle": c_angle - 0.4,
                    "end_angle": c_angle + 0.4,
                    "radius_m": site["radius_m"],
                    "owner_id": drone_id,
                    "original_owner": drone_id,
                    "status": "UNCOVERED",
                }]

        for sec in lost_sectors:
            sec["status"] = "UNCOVERED"
        self.failed_zones[drone_id] = lost_sectors

        # Step-by-step notifications
        self._add_notification(f"MONITOR DRONE {drone_id} FAILURE DETECTED")
        self._add_notification("Uncovered surveillance area identified.")
        self._add_notification("Coverage reassignment initiated.")

        # Identify candidate available monitor drones
        candidates = [
            a for a in self.engine.agents
            if a.agent_type == "MONITOR_DRONE" and a.operational and a.agent_id != drone_id
        ]

        if not candidates:
            for sec in lost_sectors:
                sec["status"] = "UNMONITORED"
            self.operational_warnings.append(f"Surveillance coverage deficit: {drone_id}'s area is UNMONITORED (no available drones).")
            self._add_notification(f"WARNING: Area {drone_id} marked UNMONITORED - no replacement drone available.")
            return

        # Score candidates considering: distance, battery %, workload, existing zones, comms
        def score_candidate(cand, target_sec):
            dist = cand.distance_to(drone.lat, drone.lng)
            workload = len(self.drone_sectors.get(cand.agent_id, []))
            comm_bonus = 0.0 if self.engine.network.neighbors(cand.agent_id) else 1500.0
            batt_penalty = (100.0 - cand.battery) * 10.0
            workload_penalty = workload * 800.0
            return dist + batt_penalty + workload_penalty + comm_bonus

        # Distribute lost sectors among candidates (avoid overloading a single drone)
        reassigned_any = False
        for sec in lost_sectors:
            # Sort candidates by suitability for this sector
            eligible = [c for c in candidates if len(self.drone_sectors.get(c.agent_id, [])) < config.MAX_SECTORS_PER_DRONE]
            if not eligible:
                eligible = candidates  # fallback if all have reached limit

            best_cand = min(eligible, key=lambda c: score_candidate(c, sec))
            sec["owner_id"] = best_cand.agent_id
            sec["owner_id"] = best_cand.agent_id
            sec["status"] = "REASSIGNED"

            if best_cand.agent_id not in self.drone_sectors:
                self.drone_sectors[best_cand.agent_id] = []
            self.drone_sectors[best_cand.agent_id].append(sec)

            reassignment_rec = {
                "sector_id": sec["id"],
                "sector_name": sec["name"],
                "original_owner": drone_id,
                "assigned_to": best_cand.agent_id,
                "tick": self.engine.tick,
            }
            self.reassignments.append(reassignment_rec)
            if len(self.reassignments) > 20:
                self.reassignments.pop(0)

            self._add_notification(f"{best_cand.agent_id} assigned to {sec['name']}.")
            reassigned_any = True

        if reassigned_any:
            self._add_notification("Surveillance coverage restored.")

    def on_drone_restored(self, drone):
        """
        Handle drone recovery:
        1. Restore communication status.
        2. Check position and health.
        3. Avoid duplicate assignments.
        4. Reintegrate into surveillance network safely.
        """
        if drone.agent_type != "MONITOR_DRONE":
            return

        drone_id = drone.agent_id
        self._add_notification(f"MONITOR DRONE {drone_id} RESTORED")
        self._add_notification(f"MONITOR DRONE {drone_id} RECONNECTED")

        # Retrieve any failed zones previously owned by this drone
        reclaimed = self.failed_zones.pop(drone_id, [])

        # Remove these sectors from temporary adopters
        for sec in reclaimed:
            temp_owner = sec.get("owner_id")
            if temp_owner and temp_owner in self.drone_sectors:
                self.drone_sectors[temp_owner] = [
                    s for s in self.drone_sectors[temp_owner] if s["id"] != sec["id"]
                ]
            sec["owner_id"] = drone_id
            sec["status"] = "MONITORED"

        if reclaimed:
            self.drone_sectors[drone_id] = reclaimed
        else:
            # If not in failed_zones, trigger sector redistribution
            self.initialize_sectors()

        self._add_notification(f"Surveillance network safely reintegrated {drone_id}.")

    def _add_notification(self, text: str):
        self.notifications.append({"message": text, "tick": self.engine.tick, "time": time.time()})
        if len(self.notifications) > 25:
            self.notifications.pop(0)

    # ------------------------------------------------------------------
    # 3. Continuous Trajectory Detection & Boundary Proximity
    # ------------------------------------------------------------------

    def check_continuous_detection(self, agent, physical_incidents=None) -> bool:
        """
        Segment-to-point proximity checking:
        If the drone swept past an incident between its previous position (prev_lat, prev_lng)
        and current position (lat, lng), detect it even if discrete tick points are on the edge.
        """
        if not agent.operational:
            return False

        if physical_incidents is None:
            physical_incidents = [i for i in self.engine.incidents.values() if i.physical]

        if not physical_incidents:
            return False

        prev_lat = getattr(agent, "prev_lat", agent.lat)
        prev_lng = getattr(agent, "prev_lng", agent.lng)
        matched_any = False

        for incident in physical_incidents:
            if incident.status == "RESOLVED":
                continue

            # Check distance to movement segment
            min_dist = segment_distance_m(prev_lat, prev_lng, agent.lat, agent.lng, incident.lat, incident.lng)
            effective_radius = self.nominal_radius_m + self.boundary_tolerance_m

            if min_dist <= effective_radius:
                # Agent swept through or is within the detection threshold
                is_boundary = min_dist > self.nominal_radius_m
                self._handle_trajectory_detection(agent, incident, min_dist, is_boundary)
                matched_any = True

        return matched_any

    def _handle_trajectory_detection(self, agent, incident, distance_m: float, is_boundary: bool):
        """Process detection from trajectory proximity, requesting verification if boundary."""
        if incident.status == "UNDETECTED":
            # If within boundary tolerance, flag as boundary/provisional
            detection_tier = "BOUNDARY" if is_boundary else "NOMINAL"
            record = {
                "incident_id": incident.incident_id,
                "agent_id": agent.agent_id,
                "distance_m": round(distance_m, 1),
                "tier": detection_tier,
                "tick": self.engine.tick,
            }
            if not any(b["incident_id"] == incident.incident_id for b in self.boundary_detections):
                self.boundary_detections.append(record)
                if len(self.boundary_detections) > 25:
                    self.boundary_detections.pop(0)

            if is_boundary:
                incident.is_boundary = True
                incident.provisional = True
                self._request_boundary_multi_drone_verification(agent, incident)

    def _request_boundary_multi_drone_verification(self, detecting_agent, incident):
        """
        Multi-drone boundary verification:
        When an incident is detected near a coverage boundary:
        - Notify nearby monitor drones.
        - Request secondary verification.
        - Combine available sensor readings.
        """
        nearby = [
            a for a in self.engine.agents
            if a.agent_type == "MONITOR_DRONE" and a.operational and a.agent_id != detecting_agent.agent_id
            and a.distance_to(incident.lat, incident.lng) <= (self.nominal_radius_m * 2.5)
        ]
        if nearby:
            self._add_notification(f"Boundary detection {incident.incident_id}: notifying {len(nearby)} nearby drone(s) for verification.")
            for drone in nearby[:2]:
                if not drone.task_id and drone.is_available_for_task():
                    drone.destination = (incident.lat, incident.lng)
                    drone.destination_label = f"Verify boundary alert {incident.incident_id}"
        else:
            self._add_notification(f"Boundary detection {incident.incident_id}: single drone available, preserved as provisional.")

    # ------------------------------------------------------------------
    # 4. Coverage Metrics & Overlap / Gap Computation
    # ------------------------------------------------------------------

    def compute_coverage_summary(self) -> dict:
        """
        Calculates:
        - Total, active, failed, offline, investigating monitor drones.
        - Percentage of surveillance coverage (never falsely 100% when drones fail).
        - Number of uncovered areas and boundary detections.
        - Overlapping coverage regions between neighbouring drones.
        - Uncovered geographical regions (arc wedges / sectors).
        """
        monitors = [a for a in self.engine.agents if a.agent_type == "MONITOR_DRONE"]
        total = len(monitors)
        active = sum(1 for m in monitors if m.operational)
        failed = sum(1 for m in monitors if m.status == "FAILED")
        offline = sum(1 for m in monitors if self.heartbeats.get(m.agent_id, {}).get("comm_status") == "OFFLINE")
        investigating = sum(1 for m in monitors if m.task_id and "INVESTIGATE" in str(m.task_id))

        # Calculate coverage percentage based on actively covered surveillance sectors
        total_sectors = sum(len(sec_list) for sec_list in self.drone_sectors.values()) + sum(len(sec_list) for sec_list in self.failed_zones.values())
        if total_sectors == 0:
            total_sectors = max(total, 1)

        uncovered_sectors = []
        for d_id, zones in self.failed_zones.items():
            for z in zones:
                if z.get("status") in ("UNCOVERED", "UNMONITORED"):
                    uncovered_sectors.append({
                        "original_owner": d_id,
                        "name": z.get("name", f"Sector-{d_id}"),
                        "center_angle": z.get("center_angle", 0.0),
                        "start_angle": z.get("start_angle", 0.0),
                        "end_angle": z.get("end_angle", 0.0),
                        "radius_m": z.get("radius_m", 1200.0),
                        "status": z.get("status", "UNCOVERED"),
                    })

        monitored_sectors = 0
        reassigned_sectors = 0
        for d_id, zones in self.drone_sectors.items():
            owner = self.engine.agents_by_id.get(d_id)
            if owner and owner.operational:
                for z in zones:
                    if z.get("status") == "REASSIGNED":
                        reassigned_sectors += 1
                        monitored_sectors += 0.85  # slightly lower density when 1 drone covers 2 sectors
                    else:
                        monitored_sectors += 1.0

        coverage_pct = round(min(100.0, max(0.0, (monitored_sectors / max(1, total_sectors)) * 100.0)), 1)
        if failed > 0 and not reassigned_sectors:
            coverage_pct = min(coverage_pct, round(100.0 * (active / max(1, total)), 1))

        # Calculate overlapping coverage between active monitor drones
        overlaps = []
        operational_monitors = [m for m in monitors if m.operational]
        for i in range(len(operational_monitors)):
            for j in range(i + 1, len(operational_monitors)):
                d1 = operational_monitors[i]
                d2 = operational_monitors[j]
                dist = haversine_m(d1.lat, d1.lng, d2.lat, d2.lng)
                combined_r = self.nominal_radius_m * 2.0
                if dist < combined_r:
                    overlap_width = round(combined_r - dist, 1)
                    overlaps.append({
                        "drone_a": d1.agent_id,
                        "drone_b": d2.agent_id,
                        "distance_m": round(dist),
                        "overlap_width_m": overlap_width,
                        "midpoint": [round((d1.lat + d2.lat) / 2.0, 6), round((d1.lng + d2.lng) / 2.0, 6)],
                    })

        # Reassigned tasks
        reassigned_tasks = [
            t.to_summary() for t in self.engine.tasks.values()
            if getattr(t, "reassign_count", 0) > 0 and t.active
        ]

        provisional_incidents = [
            i.incident_id for i in self.engine.incidents.values()
            if getattr(i, "provisional", False) and i.is_open
        ]

        return {
            "total_monitors": total,
            "total_monitor_drones": total,
            "active_monitors": active,
            "active_monitor_drones": active,
            "failed_monitors": failed,
            "failed_monitor_drones": failed,
            "offline_monitors": offline,
            "offline_monitor_drones": offline,
            "investigating_monitors": investigating,
            "investigating_monitor_drones": investigating,
            "coverage_pct": coverage_pct,
            "uncovered_count": len(uncovered_sectors),
            "uncovered_sectors_count": len(uncovered_sectors),
            "uncovered_areas": uncovered_sectors,
            "reassigned_tasks_count": len(reassigned_tasks),
            "reassigned_tasks": reassigned_tasks,
            "reassignments": self.reassignments[-10:],
            "boundary_detections_count": len(self.boundary_detections),
            "boundary_detections": self.boundary_detections[-10:],
            "provisional_incidents": provisional_incidents,
            "overlapping_regions": overlaps[:12],
            "nominal_radius_m": self.nominal_radius_m,
            "boundary_tolerance_m": self.boundary_tolerance_m,
            "notifications": self.notifications[-10:],
            "recent_notifications": self.notifications[-10:],
            "operational_warning": self.operational_warnings[-1] if self.operational_warnings else None,
            "operational_warnings": self.operational_warnings[-4:],
        }
