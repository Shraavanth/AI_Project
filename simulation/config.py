"""
All tunable simulation numbers in one place.

Distances are metres, time is simulation seconds. One simulation tick is one
simulated second. Agent speeds are deliberately faster than real drones so a
complete demonstration fits into a few minutes.
"""

import os

# ------------------------------------------------------------------
# Default monitoring area (used until the browser sends a location)
# VIT Vellore campus - change with DEMO_LATITUDE / DEMO_LONGITUDE env vars.
# ------------------------------------------------------------------
DEMO_LATITUDE = float(os.getenv("DEMO_LATITUDE", "12.9692"))
DEMO_LONGITUDE = float(os.getenv("DEMO_LONGITUDE", "79.1559"))
DEMO_LABEL = os.getenv("DEMO_LABEL", "Demonstration area (VIT Vellore)")
DEFAULT_RADIUS_M = 1200.0
MIN_RADIUS_M = 400.0
MAX_RADIUS_M = 5000.0

# ------------------------------------------------------------------
# Simulation clock
# ------------------------------------------------------------------
BASE_TICK_SECONDS = 1.0                 # real seconds per tick at 1x speed
ALLOWED_SPEEDS = (0.5, 1.0, 2.0, 4.0)   # speed multipliers offered in the UI

# ------------------------------------------------------------------
# Communication network
# ------------------------------------------------------------------
COMM_RANGE_M = 600.0        # normal radio range: agents closer than this link automatically
MAX_RELAY_RANGE_M = 1000.0  # boosted range used by self-organization to bridge split clusters
HEARTBEAT_TIMEOUT_TICKS = 3     # a neighbour silent for this long (and unreachable) is declared lost
TELEMETRY_TIMEOUT_TICKS = 5     # Command Center marks an agent offline after this many silent ticks

# ------------------------------------------------------------------
# Detection and consensus
# ------------------------------------------------------------------
DETECTION_STREAK_TICKS = 2      # same hazard class must be seen on consecutive ticks before alerting
EVIDENCE_RANGE_M = 450.0        # agents farther than this from the alert point abstain (cannot observe it)
OPPOSE_RANGE_M = 300.0          # a "normal" vote only counts against the alert from this close
CONSENSUS_MIN_SUPPORT = 2       # at least two agents must independently support the hazard
CONSENSUS_THRESHOLD = 0.6       # support / (support + oppose) needed to confirm
CONSENSUS_TIMEOUT_TICKS = 40    # alert is rejected if not confirmed within this time
CONSENSUS_MIN_ROUNDS = 2        # evidence messages take a tick to arrive, so never confirm on the first round
NO_SUPPORT_REJECT_TICKS = 6     # rejected early if nobody supports it for this long
DETECTION_COOLDOWN_TICKS = 10   # after a rejection, wait before alerting again for the same hazard
GROUPING_EXTRA_M = 300.0        # alerts within incident radius + this join the same incident
MAX_INVESTIGATORS = 2
INVESTIGATION_MAX_DISTANCE_M = 2000.0
INVESTIGATION_SEARCH_M = 180.0   # investigators visit 4 points this far around the alert point

# ------------------------------------------------------------------
# Fault-tolerant drone coverage and boundary detection
# ------------------------------------------------------------------
MONITOR_NOMINAL_RADIUS_M = 450.0          # nominal detection radius of monitor drone
DETECTION_BOUNDARY_TOLERANCE_M = 80.0     # configurable boundary tolerance margin
DRONE_HEARTBEAT_TIMEOUT_TICKS = 4         # timeout for drone health monitoring
MAX_SECTORS_PER_DRONE = 3                 # avoid overloading a single drone with reassignments

# ------------------------------------------------------------------
# Movement, battery
# ------------------------------------------------------------------
ARRIVAL_DISTANCE_M = 40.0
BATTERY_MOVE_COST_PER_M = 0.0025    # 1 km of flight costs 2.5 % battery
BATTERY_IDLE_COST = 0.005           # per tick, electronics only
BATTERY_RESPOND_COST = 0.15         # per tick while performing a response action
BATTERY_CHARGE_RATE = 1.0           # per tick while parked at home base
LOW_BATTERY_RETURN = 20.0           # below this an idle mobile agent returns home to charge
MIN_TASK_BATTERY = 25.0             # agents below this are not given new response tasks
CHARGE_UNTIL = 95.0
RECOVERY_TICKS = 3                  # a restored agent reboots for this many ticks
COMPLETED_HOLD_TICKS = 2            # agents show COMPLETED briefly after finishing a task
TRAIL_LENGTH = 15

# ------------------------------------------------------------------
# Incidents (environment)
# ------------------------------------------------------------------
INCIDENT_DEFAULTS = {
    "FIRE": {"radius_m": 400.0, "severity": 70.0},
    "POLLUTION": {"radius_m": 450.0, "severity": 70.0},
    "EXTREME_HEAT": {"radius_m": 700.0, "severity": 80.0},
}

# Change applied to a sensor at the centre of a severity-100 incident.
# The change fades with distance (Gaussian profile, see environment.py).
SENSOR_EFFECTS = {
    "FIRE": {"temperature": 32.0, "humidity": -75.0, "smoke": 0.95,
             "co2": 750.0, "air_quality": 90.0, "soil_moisture": -30.0},
    "POLLUTION": {"temperature": 2.0, "humidity": 0.0, "smoke": 0.60,
                  "co2": 1100.0, "air_quality": 230.0, "soil_moisture": 0.0},
    "EXTREME_HEAT": {"temperature": 34.0, "humidity": -35.0, "smoke": 0.0,
                     "co2": 0.0, "air_quality": 0.0, "soil_moisture": -25.0},
}
EFFECT_FALLOFF = 1.2           # influence = intensity * exp(-FALLOFF * (d / radius)^2)
SENSOR_SMOOTHING = 0.5         # readings move this fraction toward the new value each tick

FIRE_GROWTH_PER_TICK = 0.12    # an untreated fire slowly gets worse
RESOLVED_SEVERITY = 3.0        # incident is resolved when severity falls to this level
NEEDS_INTERVENTION_TICKS = 15  # confirmed incident with no working responder for this long
ACTION_RANGE_M = 120.0         # responder must be within (radius * 0.8 + this) of the hazard centre
NONPHYSICAL_CLEAR_TICKS = 10   # agent-reported incident with no supporting readings closes after this

# Response units requested per hazard type: (capability, count, optional)
RESPONSE_PLAN = {
    "FIRE": [("FIRE_SUPPRESSION", 2, False), ("WATER_SPRAY", 2, True)],
    "POLLUTION": [("POLLUTION_CLEANUP", 2, False)],
    "EXTREME_HEAT": [("COOLING", 1, False)],
}

# ------------------------------------------------------------------
# Persistence sampling (to avoid writing the database every tick)
# ------------------------------------------------------------------
TELEMETRY_SAMPLE_TICKS = 5
SEVERITY_SAMPLE_TICKS = 2
PROGRESS_MESSAGE_TICKS = 5
MAX_TELEMETRY_ROWS = 30000
