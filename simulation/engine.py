"""
SimulationEngine - the single source of truth for the whole simulation.

One call to step() advances the world by one tick (one simulated second):

    1. Environment      incident dynamics (an untreated fire grows)
    2. Sensing          every operational agent updates its six readings
    3. Local AI         Isolation Forest + rule classifier for every agent (one batch)
    4. Network          rebuild links from real positions, self-organize, heartbeats
    5. Failure checks   lost neighbours (peer heartbeat), lost telemetry (Command Center)
    6. Detection        persistent local anomalies raise INCIDENT_ALERTs
    7. Coordination     consensus, investigation, task allocation, reassignment
    8. Behaviour        movement, patrol, response actions, battery
    9. Incident status  RESPONDING / RESOLVED / NEEDS_INTERVENTION
   10. Telemetry        report to the Command Center (sampled for the database)

The engine has no web or database code. The backend calls step() from a
background loop and drains engine.outbox to persist records.
"""

import math
import random
from collections import deque
from datetime import datetime, timezone

from agents import self_organization
from agents.agent import (
    Agent, COMPLETED, COORDINATING, DETECTING, FAILED, IDLE, MOVING,
    PATROLLING, RECOVERING, RESPONDING, RETURNING,
)
from agents.agent_types import AGENT_TYPES, DEFAULT_FLEET_ORDER
from agents.communication import CommunicationManager
from ai.anomaly_detector import validate_readings
from ai.event_classifier import analyze_batch
from network.network_manager import NetworkManager
from simulation import config, coordination
from simulation.coverage_manager import CoverageManager
from simulation.environment import (
    ACTIVE_RESPONSE_STATUSES, CONFIRMED, NEEDS_INTERVENTION, RESOLVED, RESPONDING as INC_RESPONDING,
    UNDETECTED, Incident, SENSOR_NOISE, clip_readings, random_baseline,
)
from simulation.geo import haversine_m, ring_point
from simulation import tasks as T

INCIDENT_TYPES = ("FIRE", "POLLUTION", "EXTREME_HEAT")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Outbox:
    """Records produced during a tick, waiting to be written to the database."""

    def __init__(self):
        self.clear()

    def clear(self):
        self.activity = []
        self.consensus = []
        self.task_events = []
        self.failures = {}          # failure_id -> latest record
        self.network_events = []
        self.severity = []
        self.telemetry = []
        self.incidents = set()      # incident ids whose record changed
        self.tasks = set()          # task ids whose record changed
        self.site = None

    def drain(self) -> dict:
        data = {
            "activity": self.activity,
            "consensus": self.consensus,
            "task_events": self.task_events,
            "failures": list(self.failures.values()),
            "network_events": self.network_events,
            "severity": self.severity,
            "telemetry": self.telemetry,
            "incidents": set(self.incidents),
            "tasks": set(self.tasks),
            "site": self.site,
        }
        self.clear()
        return data


class SimulationEngine:

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.network = NetworkManager()
        self.comms = CommunicationManager(self.network)
        self.coverage = CoverageManager(self)
        self.outbox = Outbox()
        self.agents = []
        self.agents_by_id = {}
        self.incidents = {}
        self.tasks = {}
        self.failures = {}              # failure_id -> record
        self.open_failure_by_agent = {}
        self.site = None
        self.tick = 0
        self.running = True
        self.speed = 1.0
        self.run_id = 0
        self.recent_activity = deque(maxlen=250)
        self.network_events = deque(maxlen=40)
        self.last_network_info = {}
        self.link_churn = 0
        self.resolved_count = 0
        self._incident_counter = 0
        self._task_counter = 0
        self._failure_counter = 0
        self.last_step_ms = 0.0

    # ==============================================================
    # Logging helpers
    # ==============================================================

    def log(self, category, title, message, agent_id=None, incident_id=None, details=None):
        entry = {
            "tick": self.tick,
            "timestamp": utc_now(),
            "category": category,
            "title": title,
            "message": message,
            "agent_id": agent_id,
            "incident_id": incident_id,
            "details": details or {},
        }
        self.recent_activity.appendleft(entry)
        self.outbox.activity.append(entry)
        return entry

    def task_event(self, task, event, from_agent=None, to_agent=None, reason=""):
        self.outbox.task_events.append({
            "tick": self.tick,
            "timestamp": utc_now(),
            "task_id": task.task_id,
            "incident_id": task.incident_id,
            "task_type": task.task_type,
            "event": event,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "reason": reason,
        })
        self.outbox.tasks.add(task.task_id)

    # ==============================================================
    # Deployment and fleet management
    # ==============================================================

    def deploy(self, lat, lng, radius_m=config.DEFAULT_RADIUS_M, label="Monitoring area", source="DEMO"):
        if not (-85 <= lat <= 85 and -180 <= lng <= 180):
            raise ValueError("Latitude/longitude out of range")
        if not (config.MIN_RADIUS_M <= radius_m <= config.MAX_RADIUS_M):
            raise ValueError(f"Radius must be between {config.MIN_RADIUS_M:.0f} and {config.MAX_RADIUS_M:.0f} m")

        self.run_id += 1
        self.tick = 0
        self.agents, self.agents_by_id = [], {}
        self.incidents, self.tasks = {}, {}
        self.failures, self.open_failure_by_agent = {}, {}
        self.comms.reset()
        self.network = NetworkManager()
        self.comms.network = self.network
        self.network_events.clear()
        self.recent_activity.clear()
        self.resolved_count = 0
        self.link_churn = 0
        # ids embed the run number (INC-<run><n>), so counters can restart every run
        self._incident_counter = 0
        self._task_counter = 0
        self._failure_counter = 0

        self.site = {
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "radius_m": float(radius_m),
            "label": (label or "Monitoring area").strip()[:120],
            "source": source,
            "run_id": self.run_id,
            "deployed_at": utc_now(),
        }
        self.outbox.site = dict(self.site)

        # Sunflower (golden-angle) placement: even spread, no two agents on the same spot
        golden_angle = math.pi * (3 - math.sqrt(5))
        count = len(DEFAULT_FLEET_ORDER)
        type_counters = {}
        for index, agent_type in enumerate(DEFAULT_FLEET_ORDER):
            distance = radius_m * 0.85 * math.sqrt((index + 0.5) / count)
            angle = index * golden_angle
            a_lat, a_lng = ring_point(lat, lng, distance, angle)
            type_counters[agent_type] = type_counters.get(agent_type, 0) + 1
            agent_id = f"{AGENT_TYPES[agent_type]['prefix']}-{type_counters[agent_type]:02d}"
            self._add_agent_object(Agent(agent_id, agent_type, a_lat, a_lng, random_baseline(self.rng)))

        self._assign_patrol_routes()
        self.coverage.initialize_sectors()
        info = self._rebuild_network()
        self.log("SIMULATION", "Fleet deployed",
                 f"{len(self.agents)} agents deployed around {self.site['label']} "
                 f"(radius {radius_m:.0f} m). Network: {info['edges']} links, "
                 f"{'connected' if info['connected'] else str(info['components']) + ' clusters'}.",
                 details={"radius_m": radius_m, "source": source, "agents": len(self.agents)})
        return self.snapshot()

    def reset(self):
        site = self.site or {"lat": config.DEMO_LATITUDE, "lng": config.DEMO_LONGITUDE,
                             "radius_m": config.DEFAULT_RADIUS_M, "label": config.DEMO_LABEL, "source": "DEMO"}
        return self.deploy(site["lat"], site["lng"], site["radius_m"], site["label"], site["source"])

    def _add_agent_object(self, agent):
        self.agents.append(agent)
        self.agents_by_id[agent.agent_id] = agent

    def _assign_patrol_routes(self):
        """Give operational monitoring drones dynamically balanced sectors covering the full area."""
        monitors = [a for a in self.agents if a.agent_type == "MONITOR_DRONE" and a.operational]
        if not monitors or not self.site:
            return
        c_lat, c_lng = self.site["lat"], self.site["lng"]
        monitors.sort(key=lambda d: math.atan2(d.lat - c_lat, d.lng - c_lng))
        sector = 2 * math.pi / len(monitors)
        r = self.site["radius_m"]
        for i, drone in enumerate(monitors):
            centre_angle = i * sector
            route = []
            for k in range(6):
                angle = centre_angle - sector * 0.45 + sector * 0.9 * (k / 5)
                distance = r * (0.35 if k % 2 == 0 else 0.85) * self.rng.uniform(0.9, 1.05)
                route.append(ring_point(c_lat, c_lng, distance, angle))
            drone.patrol_route = route
            if drone.patrol_route:
                drone.patrol_index = min(range(len(route)), key=lambda idx: drone.distance_to(*route[idx]))

    def add_agent(self, agent_type, agent_id=None, lat=None, lng=None):
        if agent_type not in AGENT_TYPES:
            raise ValueError(f"Unknown agent type {agent_type}")
        if agent_id and agent_id in self.agents_by_id:
            raise ValueError(f"Agent {agent_id} already exists")
        if agent_id is None:
            n = sum(1 for a in self.agents if a.agent_type == agent_type) + 1
            agent_id = f"{AGENT_TYPES[agent_type]['prefix']}-{n:02d}"
            while agent_id in self.agents_by_id:
                n += 1
                agent_id = f"{AGENT_TYPES[agent_type]['prefix']}-{n:02d}"
        if lat is None or lng is None:
            lat, lng = ring_point(self.site["lat"], self.site["lng"],
                                  self.rng.uniform(0.1, 0.8) * self.site["radius_m"],
                                  self.rng.uniform(0, 2 * math.pi))
        else:
            self._check_inside_area(lat, lng)
        agent = Agent(agent_id, agent_type, lat, lng, random_baseline(self.rng))
        self._add_agent_object(agent)
        if agent_type == "MONITOR_DRONE":
            self._assign_patrol_routes()
        self._rebuild_network(trigger="AGENT_ADDED", agent_id=agent_id)
        self.log("AGENT", f"Agent added: {agent_id}", f"{agent.type_info['label']} {agent_id} joined the fleet.",
                 agent_id=agent_id)
        return agent

    def remove_agent(self, agent_id):
        agent = self.get_agent(agent_id)
        if agent.task_id and self.tasks.get(agent.task_id) and self.tasks[agent.task_id].active:
            raise ValueError(f"{agent_id} is working on {agent.task_id}; fail it instead to trigger reassignment")
        self.agents.remove(agent)
        del self.agents_by_id[agent_id]
        if agent.agent_type == "MONITOR_DRONE":
            self._assign_patrol_routes()
        self._rebuild_network(trigger="AGENT_REMOVED", agent_id=agent_id)
        self.log("AGENT", f"Agent removed: {agent_id}", f"{agent_id} was decommissioned.", agent_id=agent_id)

    def get_agent(self, agent_id) -> Agent:
        agent = self.agents_by_id.get(agent_id)
        if agent is None:
            raise KeyError(f"Agent {agent_id} not found")
        return agent

    def _check_inside_area(self, lat, lng, factor=1.5):
        if not self.site:
            raise ValueError("No monitoring area deployed")
        limit = self.site["radius_m"] * factor
        d = haversine_m(lat, lng, self.site["lat"], self.site["lng"])
        if d > limit:
            raise ValueError(f"Location is {d:.0f} m from the area centre; must be within {limit:.0f} m")

    # ==============================================================
    # Operator actions
    # ==============================================================

    def create_incident(self, incident_type, lat, lng, radius_m=None, severity=None):
        incident_type = incident_type.upper()
        if incident_type not in INCIDENT_TYPES:
            raise ValueError(f"Incident type must be one of {', '.join(INCIDENT_TYPES)}")
        self._check_inside_area(lat, lng)
        defaults = config.INCIDENT_DEFAULTS[incident_type]
        radius_m = float(radius_m or defaults["radius_m"])
        severity = float(severity or defaults["severity"])
        if not (100 <= radius_m <= 1500):
            raise ValueError("Incident radius must be between 100 and 1500 m")
        if not (10 <= severity <= 100):
            raise ValueError("Severity must be between 10 and 100")

        incident = Incident(self._next_incident_id(), incident_type, lat, lng, radius_m, severity,
                            origin="OPERATOR", tick=self.tick, physical=True)
        incident.add_timeline(self.tick, "CREATED",
                              f"{incident_type} created by operator (severity {severity:.0f}, radius {radius_m:.0f} m). "
                              "Agents have not detected it yet.")
        self.incidents[incident.incident_id] = incident
        self.outbox.incidents.add(incident.incident_id)
        self.log("INCIDENT", f"{incident_type} started", f"{incident.incident_id}: simulated {incident_type.lower().replace('_', ' ')} "
                 f"placed in the environment. Waiting for agents' sensors to notice it.",
                 incident_id=incident.incident_id)
        return incident

    def _next_incident_id(self):
        self._incident_counter += 1
        return f"INC-{self.run_id:02d}{self._incident_counter:03d}"

    def next_task_id(self):
        self._task_counter += 1
        return f"TSK-{self.run_id:02d}{self._task_counter:04d}"

    def fail_agent(self, agent_id, reason="MANUAL"):
        agent = self.get_agent(agent_id)
        if agent.status == FAILED:
            raise ValueError(f"Agent {agent_id} is already FAILED")
        self._fail(agent, reason)
        return agent

    def _fail(self, agent, reason):
        """Stop an agent completely and record everything that changes because of it."""
        was_status = agent.status
        task = self.tasks.get(agent.task_id) if agent.task_id else None

        agent.status = FAILED
        agent.failure_reason = reason
        agent.failed_tick = self.tick
        agent.destination = None
        agent.destination_label = None
        agent.hold_status = None
        agent.last_heard = {}
        agent.charging = False

        if task and task.active and task.status != T.INTERRUPTED:
            task.status = T.INTERRUPTED
            task.interrupted_tick = self.tick
            self.task_event(task, "INTERRUPTED", from_agent=agent.agent_id,
                            reason=f"owner failed ({reason.lower()})")
            incident = self.incidents.get(task.incident_id)
            if incident:
                incident.add_timeline(self.tick, "TASK_INTERRUPTED",
                                      f"{agent.agent_id} failed during {task.task_type} - task {task.task_id} interrupted.")
                self.outbox.incidents.add(incident.incident_id)

        self._failure_counter += 1
        failure = {
            "failure_id": f"FLR-{self.run_id:02d}{self._failure_counter:03d}",
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "reason": reason,
            "status_before": was_status,
            "lat": round(agent.lat, 6),
            "lng": round(agent.lng, 6),
            "task_id": task.task_id if task else None,
            "incident_id": task.incident_id if task else None,
            "failed_tick": self.tick,
            "failed_at": utc_now(),
            "detected_tick": None,
            "detected_by": None,
            "detection_method": None,
            "command_center_tick": None,
            "reassigned_to": None,
            "reassigned_tick": None,
            "restored_tick": None,
        }
        self.failures[failure["failure_id"]] = failure
        self.open_failure_by_agent[agent.agent_id] = failure["failure_id"]
        self.outbox.failures[failure["failure_id"]] = failure

        net = self._rebuild_network(trigger="FAILURE", agent_id=agent.agent_id)
        if agent.agent_type == "MONITOR_DRONE":
            self._assign_patrol_routes()
            self.coverage.on_drone_failed(agent)
            active_monitors = sum(1 for a in self.agents if a.agent_type == "MONITOR_DRONE" and a.operational)
            if active_monitors > 0:
                self.log("PATROL", "Patrol routes rebalanced",
                         f"Monitoring drone {agent.agent_id} failed. Remaining {active_monitors} active drone(s) expanded their patrol sectors to eliminate coverage gaps.",
                         agent_id=agent.agent_id)
        task_note = f" It was working on {task.task_id} ({task.task_type})." if task else ""
        self.log("FAILURE", f"Agent failed: {agent.agent_id}",
                 f"{agent.agent_id} stopped ({reason.replace('_', ' ').lower()}). Movement, sensing and radio are off; "
                 f"{len(net['removed'])} links removed, {len(net['relay_links'])} relay links formed."
                 f"{task_note}", agent_id=agent.agent_id,
                 incident_id=task.incident_id if task else None,
                 details={"failure_id": failure["failure_id"], "network": net})

    def restore_agent(self, agent_id):
        agent = self.get_agent(agent_id)
        if agent.status != FAILED:
            raise ValueError(f"Agent {agent_id} is not FAILED (status {agent.status})")
        agent.status = RECOVERING
        agent.recover_until_tick = self.tick + config.RECOVERY_TICKS
        agent.battery = 100.0
        agent.health = 100.0
        agent.failure_reason = None
        agent.anomaly_streak = 0
        failure_id = self.open_failure_by_agent.pop(agent_id, None)
        if failure_id:
            self.failures[failure_id]["restored_tick"] = self.tick
            self.outbox.failures[failure_id] = self.failures[failure_id]
        self.log("RECOVERY", f"Agent restored: {agent_id}",
                 f"{agent_id} restored by field crew (new battery). Rebooting for {config.RECOVERY_TICKS} s "
                 "before rejoining the network.", agent_id=agent_id)
        return agent

    def move_agent(self, agent_id, lat, lng):
        agent = self.get_agent(agent_id)
        if not agent.mobile:
            raise ValueError(f"{agent_id} is a fixed {agent.type_info['short'].lower()} and cannot move")
        if not agent.operational:
            raise ValueError(f"{agent_id} is {agent.status} and cannot move")
        if agent.task_id:
            raise ValueError(f"{agent_id} is busy with {agent.task_id}")
        self._check_inside_area(lat, lng)
        agent.destination = (lat, lng)
        agent.destination_label = "Manual move"
        agent.manual_hold_until = None
        agent.status = MOVING
        self.log("AGENT", f"Move order: {agent_id}", f"Operator sent {agent_id} to a new position "
                 f"({agent.distance_to(lat, lng):.0f} m away).", agent_id=agent_id)
        return agent

    def override_sensors(self, agent_id, readings, duration_ticks=20):
        agent = self.get_agent(agent_id)
        if not agent.operational:
            raise ValueError(f"{agent_id} is {agent.status}; its sensors are offline")
        merged = dict(agent.readings)
        merged.update({k: v for k, v in readings.items() if v is not None})
        merged = validate_readings(merged)
        agent.sensor_override = merged
        agent.override_until_tick = self.tick + int(duration_ticks)
        agent.readings = dict(merged)
        self.log("AGENT", f"Sensor override: {agent_id}",
                 f"Operator forced {agent_id}'s readings for {duration_ticks} s "
                 f"(simulated sensor fault / test).", agent_id=agent_id, details={"readings": merged})
        return agent

    def clear_sensor_override(self, agent_id):
        agent = self.get_agent(agent_id)
        agent.sensor_override = None
        agent.override_until_tick = None
        return agent

    def set_speed(self, speed):
        if speed not in config.ALLOWED_SPEEDS:
            raise ValueError(f"Speed must be one of {config.ALLOWED_SPEEDS}")
        self.speed = speed
        self.log("SIMULATION", "Speed changed", f"Simulation speed set to {speed}x.")

    def pause(self):
        self.running = False
        self.log("SIMULATION", "Paused", "Simulation paused.")

    def resume(self):
        self.running = True
        self.log("SIMULATION", "Running", "Simulation running.")

    @property
    def tick_interval(self) -> float:
        return config.BASE_TICK_SECONDS / self.speed

    # ==============================================================
    # The tick
    # ==============================================================

    def step(self):
        if not self.site:
            return
        import time
        started = time.perf_counter()
        self.tick += 1

        self._update_environment()
        self._update_sensors()
        self._run_local_ai()
        info = self._rebuild_network()
        self.link_churn += len(info["added"]) + len(info["removed"])
        self.coverage.record_heartbeats()
        self.coverage.check_heartbeat_timeouts()
        self._exchange_heartbeats()
        self_organization.detect_lost_neighbors(self)
        self_organization.check_command_center_telemetry(self)
        coordination.process_detections(self)
        coordination.coordinate_incidents(self)
        self._behave()
        self._update_incident_status()
        self._finish_transients()
        self._report_telemetry()

        self.last_step_ms = round((time.perf_counter() - started) * 1000, 2)

    # -------------------------------------------------------------- 1
    def _update_environment(self):
        for incident in self.incidents.values():
            if incident.physical and incident.is_open and incident.incident_type == "FIRE":
                incident.severity = min(100.0, incident.severity + config.FIRE_GROWTH_PER_TICK)
                incident.peak_severity = max(incident.peak_severity, incident.severity)

    # -------------------------------------------------------------- 2
    def _update_sensors(self):
        physical = [i for i in self.incidents.values() if i.physical and i.status != RESOLVED]
        for agent in self.agents:
            if not agent.operational:
                continue
            if agent.sensor_override is not None:
                if self.tick <= agent.override_until_tick:
                    agent.readings = dict(agent.sensor_override)
                    continue
                agent.sensor_override = None
                self.log("AGENT", f"Sensor override ended: {agent.agent_id}",
                         f"{agent.agent_id} is reading its real environment again.", agent_id=agent.agent_id)
            target = {k: v + self.rng.gauss(0, SENSOR_NOISE[k]) for k, v in agent.baseline.items()}
            for incident in physical:
                influence = incident.influence_at(agent.lat, agent.lng)
                d = haversine_m(agent.lat, agent.lng, incident.lat, incident.lng)
                effective_r = incident.radius_m + config.DETECTION_BOUNDARY_TOLERANCE_M
                if d <= effective_r:
                    norm_d = min(1.0, d / max(1.0, incident.radius_m))
                    boundary_factor = 1.0 if d <= incident.radius_m else max(0.35, 1.0 - (d - incident.radius_m) / config.DETECTION_BOUNDARY_TOLERANCE_M)
                    calc_influence = (incident.severity / 100.0) * math.exp(-config.EFFECT_FALLOFF * norm_d ** 2) * boundary_factor
                    influence = max(influence, calc_influence)

                if influence > 0.001:
                    for sensor, change in config.SENSOR_EFFECTS[incident.incident_type].items():
                        target[sensor] += change * influence
            target = clip_readings(target)
            for sensor, value in target.items():
                current = agent.readings[sensor]
                agent.readings[sensor] = current + config.SENSOR_SMOOTHING * (value - current)

    # -------------------------------------------------------------- 3
    def _run_local_ai(self):
        operational = [a for a in self.agents if a.operational]
        results = analyze_batch([a.readings for a in operational])
        for agent, result in zip(operational, results):
            agent.ai_result = result
            event = result["event"]
            if result["status"] == "ANOMALY" and event not in ("None", "OTHER_ANOMALY"):
                if event == agent.streak_event:
                    agent.anomaly_streak += 1
                else:
                    agent.streak_event = event
                    agent.anomaly_streak = 1
            else:
                agent.streak_event = None
                agent.anomaly_streak = 0

    # -------------------------------------------------------------- 4
    def _rebuild_network(self, trigger=None, agent_id=None) -> dict:
        info = self.network.rebuild(self.agents)
        for agent in self.agents:
            agent.neighbors = self.network.neighbors(agent.agent_id) if agent.operational else []
        self.last_network_info = info
        if trigger:
            event = {
                "tick": self.tick,
                "timestamp": utc_now(),
                "trigger": trigger,
                "agent_id": agent_id,
                "links_removed": [list(e) for e in info["removed"]],
                "links_created": [list(e) for e in info["added"]],
                "relay_links": info["relay_links"],
                "components_before_bridging": info["components_before_bridging"],
                "components_after": info["components"],
                "connected_after": info["connected"],
                "edges_after": info["edges"],
                "operational_agents": sum(1 for a in self.agents if a.operational),
                "compute_ms": info["compute_ms"],
            }
            self.network_events.appendleft(event)
            self.outbox.network_events.append(event)
            if trigger in ("FAILURE", "RESTORE"):
                state = "connected" if info["connected"] else f"PARTITIONED into {info['components']} clusters"
                self.log("NETWORK", "Network reorganized",
                         f"After {trigger.lower()} of {agent_id}: {len(info['removed'])} links removed, "
                         f"{len(info['added'])} links created ({len(info['relay_links'])} relay). "
                         f"Network is {state}. Recomputed in {info['compute_ms']} ms.",
                         agent_id=agent_id, details=event)
        return info

    def _exchange_heartbeats(self):
        for agent in self.agents:
            if agent.operational:
                for neighbor_id in agent.neighbors:
                    agent.last_heard[neighbor_id] = self.tick

    # -------------------------------------------------------------- 8
    def _behave(self):
        for agent in list(self.agents):
            if not agent.operational:
                continue
            agent.prev_lat = agent.lat
            agent.prev_lng = agent.lng
            if agent.battery <= 0:
                self._fail(agent, "BATTERY_DEPLETED")
                continue

            agent.charging = False
            task = self.tasks.get(agent.task_id) if agent.task_id else None
            if task is not None and task.active and task.owner_id == agent.agent_id:
                self._work_on_task(agent, task)
            else:
                self._behave_without_task(agent)

            agent.drain(config.BATTERY_IDLE_COST)

        physical = [i for i in self.incidents.values() if i.physical and i.status != RESOLVED]
        for agent in self.agents:
            if agent.agent_type == "MONITOR_DRONE":
                self.coverage.check_continuous_detection(agent, physical)

    def _show(self, agent, status):
        """Set a status unless a short-lived status (COMPLETED / COORDINATING) is being shown."""
        if not agent.holding(self.tick):
            agent.status = status

    def _work_on_task(self, agent, task):
        incident = self.incidents.get(task.incident_id)
        if incident is None:
            return
        target = incident.best_location()
        task.target = target
        if task.start_distance_m is None:
            task.start_distance_m = max(1.0, agent.distance_to(*target))

        if task.task_type == "INVESTIGATE":
            # Fly to the alert point, then search four points around it so the
            # incident position estimate can move toward the strongest readings.
            if task.arrived_tick is None:
                arrived = agent.step_towards(*target)
                agent.destination, agent.destination_label = target, f"Investigate {incident.incident_id}"
                task.travel_progress = max(0.0, 1 - agent.distance_to(*target) / task.start_distance_m)
                if not arrived:
                    self._show(agent, MOVING)
                    return
                task.arrived_tick = self.tick
                task.started_tick = self.tick
                task.status = T.IN_PROGRESS
                rotation = (sum(ord(c) for c in agent.agent_id) % 2) * math.pi / 4
                task.search_points = [ring_point(target[0], target[1], config.INVESTIGATION_SEARCH_M, rotation + k * math.pi / 2)
                                      for k in range(4)]
                self.task_event(task, "STARTED", to_agent=agent.agent_id, reason="arrived; searching around the alert point")
            task.travel_progress = 1.0
            points = task.search_points
            if task.search_index < len(points):
                point = points[task.search_index]
                agent.destination, agent.destination_label = point, f"Search {task.search_index + 1}/{len(points)}"
                if agent.step_towards(*point):
                    task.search_index += 1
            task.work_done = 100.0 * task.search_index / max(1, len(points))
            self._show(agent, DETECTING)
            if task.search_index >= len(points):
                coordination.complete_task(self, task, "search pattern finished")
            return

        # Response tasks
        if agent.mobile:
            arrived = agent.step_towards(*target)
        else:
            arrived = True
        agent.destination = None if arrived or not agent.mobile else target
        agent.destination_label = None if agent.destination is None else f"{task.task_type} at {incident.incident_id}"

        if not arrived:
            task.travel_progress = max(0.0, 1 - agent.distance_to(*target) / task.start_distance_m)
            self._show(agent, MOVING)
            return

        task.travel_progress = 1.0
        if task.status != T.IN_PROGRESS:
            task.status = T.IN_PROGRESS
            task.started_tick = task.started_tick or self.tick
            task.arrived_tick = self.tick
            self.task_event(task, "STARTED", to_agent=agent.agent_id, reason="on site")
            if incident.response_started_tick is None:
                incident.response_started_tick = self.tick
            incident.add_timeline(self.tick, "RESPONSE", f"{agent.agent_id} started {task.task_type} on site.")
            self.outbox.incidents.add(incident.incident_id)
            self.log("RESPONSE", f"{task.task_type.replace('_', ' ').title()} started",
                     f"{agent.agent_id} reached {incident.incident_id} and started {task.task_type.lower().replace('_', ' ')}.",
                     agent_id=agent.agent_id, incident_id=incident.incident_id)
        self._show(agent, RESPONDING)

        # The action only works if the agent is physically close to the real hazard
        d = haversine_m(agent.lat, agent.lng, incident.lat, incident.lng)
        if agent.mobile:
            effective_range = incident.radius_m * 0.8 + config.ACTION_RANGE_M
        else:
            effective_range = agent.type_info["operating_radius_m"] + incident.radius_m * 0.6
        if incident.physical and d <= effective_range and incident.severity > 0:
            reduction = min(incident.severity, agent.type_info["action_rate"])
            incident.severity -= reduction
            task.work_done += reduction
            agent.drain(config.BATTERY_RESPOND_COST)
            if incident.incident_type == "FIRE" and d < incident.radius_m * 0.5:
                agent.health = max(40.0, agent.health - 0.05)  # heat stress near the fire core
        else:
            task.ineffective_ticks += 1

        if (self.tick - task.arrived_tick) % config.PROGRESS_MESSAGE_TICKS == 0:
            coordinator = self.agents_by_id.get(incident.coordinator_id)
            if coordinator and coordinator is not agent:
                self.comms.send(self.tick, agent, coordinator, "RESPONSE_PROGRESS", incident.incident_id,
                                {"task_id": task.task_id, "severity": round(incident.severity, 1),
                                 "work_done": round(task.work_done, 1)})

    def _behave_without_task(self, agent):
        if agent.task_id:
            stale = self.tasks.get(agent.task_id)
            if stale is None or not stale.active or stale.owner_id != agent.agent_id:
                agent.task_id = None
        if agent.holding(self.tick):
            return

        # Manual move order from the operator
        if agent.destination_label == "Manual move" and agent.destination:
            if agent.step_towards(*agent.destination):
                agent.destination = None
                agent.destination_label = None
                agent.manual_hold_until = self.tick + 10
                agent.status = IDLE
            else:
                agent.status = MOVING
            return
        if agent.manual_hold_until and self.tick < agent.manual_hold_until:
            agent.status = IDLE
            return

        # Roles in incidents that are still being verified
        for incident in self.incidents.values():
            if incident.status == "DETECTED":
                if incident.coordinator_id == agent.agent_id:
                    agent.status = COORDINATING
                    agent.destination = None
                    return
                if agent.agent_id in incident.detectors:
                    agent.status = DETECTING
                    agent.destination = None
                    return

        # Low battery: go home and charge
        if agent.mobile and (agent.battery < config.LOW_BATTERY_RETURN or agent.charge_mode):
            agent.charge_mode = True
            if not agent.at_home():
                agent.step_towards(agent.home_lat, agent.home_lng)
                agent.destination = (agent.home_lat, agent.home_lng)
                agent.destination_label = "Home base (charging)"
                agent.status = RETURNING
            else:
                agent.destination = None
                agent.destination_label = None
                agent.battery = min(100.0, agent.battery + config.BATTERY_CHARGE_RATE)
                agent.charging = True
                agent.status = IDLE
                if agent.battery >= config.CHARGE_UNTIL:
                    agent.charge_mode = False
            return

        if agent.agent_type == "MONITOR_DRONE" and agent.patrol_route:
            waypoint = agent.patrol_route[agent.patrol_index]
            if agent.step_towards(*waypoint):
                agent.patrol_index = (agent.patrol_index + 1) % len(agent.patrol_route)
            agent.destination = agent.patrol_route[agent.patrol_index]
            agent.destination_label = f"Patrol waypoint {agent.patrol_index + 1}/{len(agent.patrol_route)}"
            agent.status = PATROLLING
            return

        if agent.mobile and not agent.at_home():
            agent.step_towards(agent.home_lat, agent.home_lng)
            agent.destination = (agent.home_lat, agent.home_lng)
            agent.destination_label = "Home base"
            agent.status = RETURNING
            return

        # Parked at base: top up battery slowly
        agent.destination = None
        agent.destination_label = None
        if agent.battery < 100:
            agent.battery = min(100.0, agent.battery + config.BATTERY_CHARGE_RATE * 0.3)
            agent.charging = True
        agent.status = IDLE

    # -------------------------------------------------------------- 9
    def _update_incident_status(self):
        for incident in self.incidents.values():
            if incident.status not in ACTIVE_RESPONSE_STATUSES:
                continue
            response_tasks = [self.tasks[t] for t in incident.task_ids
                              if t in self.tasks and self.tasks[t].task_type != "INVESTIGATE"]
            acting = [t for t in response_tasks if t.status == T.IN_PROGRESS
                      and self.agents_by_id.get(t.owner_id) and self.agents_by_id[t.owner_id].operational]
            en_route = [t for t in response_tasks if t.status == T.ASSIGNED
                        and self.agents_by_id.get(t.owner_id) and self.agents_by_id[t.owner_id].operational]

            if acting:
                incident.no_responder_since = None
                if incident.status != INC_RESPONDING:
                    incident.status = INC_RESPONDING
                    incident.add_timeline(self.tick, "RESPONDING",
                                          f"Response actions under way ({', '.join(t.owner_id for t in acting)}).")
                    self.outbox.incidents.add(incident.incident_id)
            elif en_route:
                incident.no_responder_since = None
                if incident.status == NEEDS_INTERVENTION:
                    incident.status = CONFIRMED
                    incident.add_timeline(self.tick, "DISPATCHED", "A capable agent became available and is on its way.")
                    self.outbox.incidents.add(incident.incident_id)
            else:
                if incident.no_responder_since is None:
                    incident.no_responder_since = self.tick
                if incident.status == INC_RESPONDING:
                    incident.status = CONFIRMED
                    incident.add_timeline(self.tick, "PAUSED", "No responder is acting on site any more.")
                    self.outbox.incidents.add(incident.incident_id)
                if (self.tick - incident.no_responder_since >= config.NEEDS_INTERVENTION_TICKS
                        and incident.status != NEEDS_INTERVENTION):
                    incident.status = NEEDS_INTERVENTION
                    incident.add_timeline(self.tick, "NEEDS_INTERVENTION",
                                          "No capable agent is available. The hazard is NOT being treated.")
                    self.outbox.incidents.add(incident.incident_id)
                    self.log("INCIDENT", "Needs intervention",
                             f"{incident.incident_id} ({incident.incident_type}) has no working responder. "
                             f"Severity {incident.severity:.0f} and {'rising' if incident.incident_type == 'FIRE' else 'not falling'}.",
                             incident_id=incident.incident_id)

            if incident.physical and incident.severity <= config.RESOLVED_SEVERITY:
                coordination.resolve_incident(self, incident,
                                              f"Severity reduced from peak {incident.peak_severity:.0f} to "
                                              f"{incident.severity:.1f} by response actions.")
            elif not incident.physical:
                supporting = [a for a in self.agents if a.operational and a.ai_result["event"] == incident.incident_type
                              and a.distance_to(*incident.best_location()) <= config.EVIDENCE_RANGE_M]
                incident.nonphysical_clear_ticks = 0 if supporting else incident.nonphysical_clear_ticks + 1
                if incident.nonphysical_clear_ticks >= config.NONPHYSICAL_CLEAR_TICKS:
                    coordination.resolve_incident(self, incident,
                                                  "No hazard found on site - readings are normal (likely a sensor fault).")

    # -------------------------------------------------------------- 10
    def _finish_transients(self):
        for agent in self.agents:
            if agent.status == RECOVERING and self.tick >= agent.recover_until_tick:
                agent.status = PATROLLING if agent.agent_type == "MONITOR_DRONE" else IDLE
                agent.recover_until_tick = None
                agent.readings = dict(agent.baseline)
                if agent.agent_type == "MONITOR_DRONE":
                    self._assign_patrol_routes()
                    self.coverage.on_drone_restored(agent)
                self._rebuild_network(trigger="RESTORE", agent_id=agent.agent_id)
                self.log("RECOVERY", f"{agent.agent_id} back online",
                         f"{agent.agent_id} finished rebooting and rejoined the network with "
                         f"{len(agent.neighbors)} neighbours.", agent_id=agent.agent_id)

    def _report_telemetry(self):
        sample = self.tick % config.TELEMETRY_SAMPLE_TICKS == 0
        for agent in self.agents:
            if not agent.operational:
                continue
            agent.last_telemetry_tick = self.tick
            if sample:
                task = self.tasks.get(agent.task_id) if agent.task_id else None
                self.outbox.telemetry.append({
                    "tick": self.tick,
                    "timestamp": utc_now(),
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "lat": round(agent.lat, 6),
                    "lng": round(agent.lng, 6),
                    "status": agent.status,
                    "battery": round(agent.battery, 1),
                    "health": round(agent.health, 1),
                    **{k: round(v, 3) for k, v in agent.readings.items()},
                    "ai_status": agent.ai_result["status"],
                    "ai_event": agent.ai_result["event"],
                    "anomaly_score": agent.ai_result["score"],
                    "task_id": task.task_id if task else None,
                    "neighbors": len(agent.neighbors),
                })
        if self.tick % config.SEVERITY_SAMPLE_TICKS == 0:
            for incident in self.incidents.values():
                if incident.physical and incident.is_open:
                    point = {"tick": self.tick, "severity": round(incident.severity, 2)}
                    incident.severity_history.append(point)
                    if len(incident.severity_history) > 600:
                        incident.severity_history = incident.severity_history[-600:]
                    acting = sum(1 for t in incident.task_ids if t in self.tasks and self.tasks[t].status == T.IN_PROGRESS
                                 and self.tasks[t].task_type != "INVESTIGATE")
                    self.outbox.severity.append({
                        "incident_id": incident.incident_id, "tick": self.tick, "timestamp": utc_now(),
                        "severity": round(incident.severity, 2), "status": incident.status, "acting_responders": acting,
                    })

    # ==============================================================
    # Read models for the API
    # ==============================================================

    def coordinator_roles(self) -> dict:
        roles = {}
        for incident in self.incidents.values():
            if incident.is_open and incident.coordinator_id:
                roles.setdefault(incident.coordinator_id, []).append(incident.incident_id)
        return roles

    def agent_dicts(self) -> list:
        roles = self.coordinator_roles()
        return [a.to_dict(self.tick, self.tasks.get(a.task_id) if a.task_id else None,
                          roles.get(a.agent_id)) for a in self.agents]

    def incident_dicts(self, include_closed=True) -> list:
        items = []
        for incident in reversed(list(self.incidents.values())):
            if not include_closed and not incident.is_open:
                continue
            tasks = [self.tasks[t] for t in incident.task_ids if t in self.tasks]
            items.append(incident.to_dict(tasks))
        return items

    def stats(self) -> dict:
        operational = [a for a in self.agents if a.operational]
        by_status = {}
        for a in self.agents:
            by_status[a.status] = by_status.get(a.status, 0) + 1
        active_tasks = [t for t in self.tasks.values() if t.active]
        return {
            "total_agents": len(self.agents),
            "operational_agents": len(operational),
            "failed_agents": by_status.get(FAILED, 0),
            "recovering_agents": by_status.get(RECOVERING, 0),
            "responding_agents": by_status.get(RESPONDING, 0),
            "moving_agents": by_status.get(MOVING, 0),
            "patrolling_agents": by_status.get(PATROLLING, 0),
            "status_counts": by_status,
            "active_incidents": sum(1 for i in self.incidents.values() if i.is_open),
            "resolved_incidents": self.resolved_count,
            "incidents_needing_intervention": sum(1 for i in self.incidents.values() if i.status == NEEDS_INTERVENTION),
            "active_tasks": len(active_tasks),
            "unassigned_tasks": sum(1 for t in active_tasks if t.status == T.UNASSIGNED),
            "links": self.network.graph.number_of_edges(),
            "relay_links": sum(1 for e in self.network.edges() if e["kind"] == "relay"),
            "network_connected": self.network.is_connected(),
            "network_components": self.network.component_count(),
            "messages_delivered": self.comms.delivered,
            "messages_dropped": self.comms.dropped,
            "average_battery": round(sum(a.battery for a in operational) / len(operational), 1) if operational else 0,
            "anomalous_agents": sum(1 for a in operational if a.ai_result["status"] == "ANOMALY"),
        }

    def simulation_state(self) -> dict:
        return {
            "tick": self.tick,
            "running": self.running,
            "speed": self.speed,
            "tick_interval_s": self.tick_interval,
            "allowed_speeds": list(config.ALLOWED_SPEEDS),
            "run_id": self.run_id,
            "last_step_ms": self.last_step_ms,
        }

    def snapshot(self) -> dict:
        return {
            "tick": self.tick,
            "simulation": self.simulation_state(),
            "site": self.site,
            "agents": self.agent_dicts(),
            "incidents": self.incident_dicts(),
            "links": self.network.edges(),
            "network": {
                "connected": self.network.is_connected(),
                "components": self.network.component_count(),
                "edges": self.network.graph.number_of_edges(),
                "comm_range_m": config.COMM_RANGE_M,
                "max_relay_range_m": config.MAX_RELAY_RANGE_M,
                "last_event": self.network_events[0] if self.network_events else None,
            },
            "stats": self.stats(),
            "coverage": self.coverage.compute_coverage_summary(),
            "activity": list(self.recent_activity)[:40],
        }

    def agent_detail(self, agent_id) -> dict:
        agent = self.get_agent(agent_id)
        data = agent.to_dict(self.tick, self.tasks.get(agent.task_id) if agent.task_id else None,
                             self.coordinator_roles().get(agent_id))
        data["type_description"] = agent.type_info["description"]
        data["baseline"] = {k: round(v, 3) for k, v in agent.baseline.items()}
        data["task"] = self.tasks[agent.task_id].to_dict() if agent.task_id in self.tasks else None
        data["task_history"] = list(reversed(agent.task_history))[:30]
        data["inbox"] = list(agent.inbox)[:30]
        data["sent"] = [m for m in self.comms.recent if m["sender"] == agent_id][:30]
        data["failures"] = [f for f in self.failures.values() if f["agent_id"] == agent_id]
        data["patrol_route"] = [[round(p[0], 6), round(p[1], 6)] for p in agent.patrol_route]
        data["neighbor_distances"] = {
            n: round(agent.distance_to(self.agents_by_id[n].lat, self.agents_by_id[n].lng))
            for n in agent.neighbors if n in self.agents_by_id
        }
        return data

    def incident_detail(self, incident_id) -> dict:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise KeyError(f"Incident {incident_id} not found")
        tasks = [self.tasks[t] for t in incident.task_ids if t in self.tasks]
        data = incident.to_dict(tasks)
        data["tasks"] = [t.to_dict() for t in tasks]
        data["timeline"] = incident.timeline
        data["consensus_history"] = incident.consensus_history
        data["severity_history"] = incident.severity_history
        data["messages"] = [m for m in self.comms.recent if m["incident_id"] == incident_id][:150]
        data["affected_agents"] = sorted(
            [{"agent_id": a.agent_id, "influence": round(incident.influence_at(a.lat, a.lng), 3),
              "distance_m": round(haversine_m(a.lat, a.lng, incident.lat, incident.lng))}
             for a in self.agents if incident.influence_at(a.lat, a.lng) > 0.05],
            key=lambda r: -r["influence"])
        return data
