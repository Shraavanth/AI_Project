"""
The simulated environment: incidents (hazards) and how they change sensor readings.

An incident created by the operator is a real hazard in the simulated world.
The agents do NOT know about it until their own sensors pick up the change.

Influence of an incident on a sensor at distance d:

    influence = (severity / 100) * exp(-EFFECT_FALLOFF * (d / radius)^2)

and every sensor value is changed by SENSOR_EFFECTS[type][sensor] * influence.
So agents near the centre see strong changes, agents near the edge see weak
changes, and agents far away see nothing. When the severity drops (because of
response actions) the influence drops too, and readings drift back to normal.
"""

import math
import random

from simulation import config
from simulation.geo import haversine_m

SENSOR_NOISE = {
    "temperature": 0.3,
    "humidity": 0.8,
    "smoke": 0.005,
    "co2": 4.0,
    "air_quality": 1.0,
    "soil_moisture": 0.4,
}

READING_LIMITS = {
    "temperature": (-30.0, 90.0),
    "humidity": (0.0, 100.0),
    "smoke": (0.0, 1.0),
    "co2": (250.0, 5000.0),
    "air_quality": (0.0, 500.0),
    "soil_moisture": (0.0, 100.0),
}

# Lifecycle of an incident record
UNDETECTED = "UNDETECTED"                 # hazard exists, no agent has noticed yet
DETECTED = "DETECTED"                     # local anomaly alert raised, consensus running
CONFIRMED = "CONFIRMED"                   # consensus reached, response being dispatched
RESPONDING = "RESPONDING"                 # at least one responder is acting on site
NEEDS_INTERVENTION = "NEEDS_INTERVENTION" # confirmed but no capable agent available
RESOLVED = "RESOLVED"
REJECTED = "REJECTED"                     # agent-reported alert rejected as false alarm

OPEN_STATUSES = {UNDETECTED, DETECTED, CONFIRMED, RESPONDING, NEEDS_INTERVENTION}
ACTIVE_RESPONSE_STATUSES = {CONFIRMED, RESPONDING, NEEDS_INTERVENTION}


def random_baseline(rng: random.Random) -> dict:
    """Normal background conditions for one agent's location."""
    temperature = rng.gauss(28.0, 1.5)
    humidity = 60.0 - 1.2 * (temperature - 28.0) + rng.gauss(0, 3.0)
    smoke = max(0.03, rng.gauss(0.10, 0.012))
    co2 = rng.gauss(420.0, 12.0)
    air_quality = 50.0 + 80.0 * (smoke - 0.10) + rng.gauss(0, 3.0)
    soil_moisture = 55.0 + 0.4 * (humidity - 60.0) + rng.gauss(0, 4.0)
    return clip_readings({
        "temperature": temperature,
        "humidity": humidity,
        "smoke": smoke,
        "co2": co2,
        "air_quality": air_quality,
        "soil_moisture": soil_moisture,
    })


def clip_readings(readings: dict) -> dict:
    return {k: max(READING_LIMITS[k][0], min(READING_LIMITS[k][1], v)) for k, v in readings.items()}


class Incident:

    def __init__(self, incident_id, incident_type, lat, lng, radius_m, severity, origin, tick, physical=True):
        self.incident_id = incident_id
        self.incident_type = incident_type
        self.lat = lat
        self.lng = lng
        self.radius_m = radius_m
        self.severity = float(severity)
        self.initial_severity = float(severity)
        self.peak_severity = float(severity)
        self.origin = origin            # OPERATOR or AGENT_REPORT
        self.physical = physical        # False = no real hazard (e.g. agent-reported sensor fault)
        self.status = UNDETECTED

        # What the agents know
        self.detectors = []             # agents whose own AI raised the alert
        self.alert_recipients = set()   # agents that received INCIDENT_ALERT
        self.estimated_location = None  # weighted centroid of detecting sensors
        self.coordinator_id = None
        self.consensus = None           # latest consensus result
        self.consensus_rounds = 0
        self.consensus_history = []
        self.last_votes = {}            # agent id -> vote (to send evidence only on change)
        self.no_support_ticks = 0
        self.rejections = 0
        self.cooldown_until = -1
        self.investigation_requested = False
        self.task_ids = []
        self.response_planned = False
        self.no_responder_since = None
        self.nonphysical_clear_ticks = 0
        self.is_boundary = False
        self.provisional = False

        # Times (simulation ticks)
        self.created_tick = tick
        self.detected_tick = None
        self.alert_tick = None
        self.confirmed_tick = None
        self.response_started_tick = None
        self.resolved_tick = None
        self.resolution_note = None

        self.timeline = []
        self.severity_history = []

    # --------------------------------------------------------------

    def influence_at(self, lat: float, lng: float) -> float:
        if not self.physical or self.status == RESOLVED or self.severity <= 0:
            return 0.0
        d = haversine_m(lat, lng, self.lat, self.lng)
        return (self.severity / 100.0) * math.exp(-config.EFFECT_FALLOFF * (d / self.radius_m) ** 2)

    def best_location(self):
        """Where responders should go: the agents' estimate if they have one."""
        if self.estimated_location is not None:
            return self.estimated_location
        return (self.lat, self.lng)

    def reference_location(self):
        """Point used to group new alerts with this incident."""
        if self.physical:
            return (self.lat, self.lng)
        return self.best_location()

    def add_timeline(self, tick: int, stage: str, text: str):
        self.timeline.append({"tick": tick, "stage": stage, "text": text})

    @property
    def is_open(self) -> bool:
        return self.status in OPEN_STATUSES

    def to_dict(self, tasks=None) -> dict:
        tasks = tasks or []
        est = self.estimated_location
        return {
            "id": self.incident_id,
            "type": self.incident_type,
            "status": self.status,
            "origin": self.origin,
            "physical": self.physical,
            "is_boundary": self.is_boundary,
            "provisional": self.provisional,
            "lat": round(self.lat, 6),
            "lng": round(self.lng, 6),
            "radius_m": round(self.radius_m),
            "severity": round(self.severity, 1),
            "initial_severity": round(self.initial_severity, 1),
            "peak_severity": round(self.peak_severity, 1),
            "estimated_location": [round(est[0], 6), round(est[1], 6)] if est else None,
            "estimate_error_m": round(haversine_m(est[0], est[1], self.lat, self.lng)) if est and self.physical else None,
            "detectors": list(self.detectors),
            "alert_recipients": sorted(self.alert_recipients),
            "coordinator_id": self.coordinator_id,
            "consensus": self.consensus,
            "consensus_rounds": self.consensus_rounds,
            "rejections": self.rejections,
            "task_ids": list(self.task_ids),
            "tasks": [t.to_summary() for t in tasks],
            "created_tick": self.created_tick,
            "detected_tick": self.detected_tick,
            "confirmed_tick": self.confirmed_tick,
            "response_started_tick": self.response_started_tick,
            "resolved_tick": self.resolved_tick,
            "resolution_note": self.resolution_note,
        }
