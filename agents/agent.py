"""
A single autonomous agent.

The agent object holds its own state (position, battery, sensors, current task,
what it has heard from neighbours). The simulation engine calls the methods in
this class every tick; decisions that need several agents (consensus, task
selection) live in consensus.py and task_allocation.py.
"""

from collections import deque

from agents.agent_types import AGENT_TYPES
from simulation import config
from simulation.geo import haversine_m, move_towards

# Status values used by the implementation
IDLE = "IDLE"                   # parked at base (response units, sprinklers) or charging
PATROLLING = "PATROLLING"       # monitoring drone following its patrol route
DETECTING = "DETECTING"         # own sensors flagged a hazard / observing an incident on site
COORDINATING = "COORDINATING"   # coordinating an incident or negotiating a task this tick
MOVING = "MOVING"               # travelling to an assigned task or a manual destination
RESPONDING = "RESPONDING"       # performing a response action at the incident
RETURNING = "RETURNING"         # travelling back to home base
FAILED = "FAILED"               # stopped: no movement, no sensing, no communication
RECOVERING = "RECOVERING"       # rebooting after being restored
COMPLETED = "COMPLETED"         # just finished a task (shown briefly)

ALL_STATUSES = [IDLE, PATROLLING, DETECTING, COORDINATING, MOVING,
                RESPONDING, RETURNING, FAILED, RECOVERING, COMPLETED]


class Agent:

    def __init__(self, agent_id: str, agent_type: str, lat: float, lng: float, baseline: dict):
        if agent_type not in AGENT_TYPES:
            raise ValueError(f"Unknown agent type {agent_type}")

        self.agent_id = agent_id
        self.agent_type = agent_type
        self.type_info = AGENT_TYPES[agent_type]

        # Position
        self.lat = lat
        self.lng = lng
        self.home_lat = lat
        self.home_lng = lng
        self.trail = deque(maxlen=config.TRAIL_LENGTH)
        self.distance_travelled_m = 0.0

        # Health
        self.status = PATROLLING if agent_type == "MONITOR_DRONE" else IDLE
        self.battery = 100.0
        self.health = 100.0
        self.failure_reason = None
        self.failed_tick = None
        self.recover_until_tick = None
        self.hold_status = None          # (status, until_tick) for short-lived statuses
        self.charging = False

        # Sensors and AI
        self.baseline = dict(baseline)
        self.readings = dict(baseline)
        self.sensor_override = None      # dict of forced readings (manual fault simulation)
        self.override_until_tick = None
        self.ai_result = {"status": "NORMAL", "event": "None", "score": 0.0}
        self.anomaly_streak = 0
        self.streak_event = None

        # Network / communication
        self.neighbors = []              # agent ids linked this tick
        self.last_heard = {}             # neighbour id -> last tick a heartbeat was received
        self.last_comm_tick = None
        self.last_telemetry_tick = None
        self.inbox = deque(maxlen=40)    # recent messages received
        self.messages_sent = 0
        self.messages_received = 0

        # Movement and tasks
        self.destination = None          # (lat, lng)
        self.destination_label = None
        self.patrol_route = []
        self.patrol_index = 0
        self.manual_hold_until = None
        self.charge_mode = False         # returning home / charging because of low battery
        self.alert_cooldown_until = -1   # after a rejected false alarm the agent waits before re-alerting
        self.task_id = None
        self.task_history = []

    # --------------------------------------------------------------
    # Basic properties
    # --------------------------------------------------------------

    @property
    def mobile(self) -> bool:
        return self.type_info["mobile"]

    @property
    def speed_mps(self) -> float:
        return self.type_info["speed_mps"]

    @property
    def capabilities(self) -> list:
        return self.type_info["capabilities"]

    @property
    def operational(self) -> bool:
        """Failed or rebooting agents do not sense, move or communicate."""
        return self.status not in (FAILED, RECOVERING)

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def is_available_for_task(self) -> bool:
        return self.operational and self.task_id is None and self.battery >= config.MIN_TASK_BATTERY

    def distance_to(self, lat: float, lng: float) -> float:
        return haversine_m(self.lat, self.lng, lat, lng)

    def at_home(self) -> bool:
        return self.distance_to(self.home_lat, self.home_lng) <= config.ARRIVAL_DISTANCE_M

    # --------------------------------------------------------------
    # Status helpers
    # --------------------------------------------------------------

    def set_status(self, status: str):
        self.status = status

    def hold(self, status: str, until_tick: int):
        """Show a short-lived status (e.g. COMPLETED, COORDINATING) until a given tick."""
        self.hold_status = (status, until_tick)
        self.status = status

    def holding(self, tick: int) -> bool:
        if self.hold_status and tick <= self.hold_status[1]:
            return True
        self.hold_status = None
        return False

    # --------------------------------------------------------------
    # Movement
    # --------------------------------------------------------------

    def step_towards(self, lat: float, lng: float, dt: float = 1.0) -> bool:
        """Move toward (lat, lng) for one tick. Returns True when arrived."""
        if not self.mobile or self.battery <= 0:
            return self.distance_to(lat, lng) <= config.ARRIVAL_DISTANCE_M
        if self.distance_to(lat, lng) <= config.ARRIVAL_DISTANCE_M:
            return True
        self.trail.append((round(self.lat, 6), round(self.lng, 6)))
        new_lat, new_lng, moved, arrived = move_towards(
            self.lat, self.lng, lat, lng, self.speed_mps * dt
        )
        self.lat, self.lng = new_lat, new_lng
        self.distance_travelled_m += moved
        self.drain(moved * config.BATTERY_MOVE_COST_PER_M)
        return arrived or self.distance_to(lat, lng) <= config.ARRIVAL_DISTANCE_M

    def drain(self, amount: float):
        self.battery = max(0.0, self.battery - amount)

    # --------------------------------------------------------------
    # Communication bookkeeping
    # --------------------------------------------------------------

    def receive(self, message: dict, tick: int):
        self.inbox.appendleft(message)
        self.messages_received += 1
        self.last_comm_tick = tick

    # --------------------------------------------------------------
    # Serialisation for the API / frontend
    # --------------------------------------------------------------

    def to_dict(self, tick: int, task=None, coordinator_of=None) -> dict:
        return {
            "id": self.agent_id,
            "type": self.agent_type,
            "type_label": self.type_info["label"],
            "mobile": self.mobile,
            "capabilities": self.capabilities,
            "operating_radius_m": self.type_info["operating_radius_m"],
            "lat": round(self.lat, 6),
            "lng": round(self.lng, 6),
            "home": [round(self.home_lat, 6), round(self.home_lng, 6)],
            "status": self.status,
            "battery": round(self.battery, 1),
            "health": round(self.health, 1),
            "charging": self.charging,
            "speed_mps": self.speed_mps,
            "readings": {k: round(v, 3 if k == "smoke" else 1) for k, v in self.readings.items()},
            "sensor_override": self.sensor_override is not None,
            "ai": self.ai_result,
            "neighbors": list(self.neighbors),
            "task_id": self.task_id,
            "task_type": task.task_type if task else None,
            "incident_id": task.incident_id if task else None,
            "task_progress": round(task.progress, 2) if task else None,
            "destination": [round(self.destination[0], 6), round(self.destination[1], 6)] if self.destination else None,
            "destination_label": self.destination_label,
            "coordinator_of": coordinator_of or [],
            "last_comm_tick": self.last_comm_tick,
            "last_telemetry_tick": self.last_telemetry_tick,
            "failure_reason": self.failure_reason,
            "trail": [list(p) for p in self.trail],
            "distance_travelled_m": round(self.distance_travelled_m),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
        }
