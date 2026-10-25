"""
The five agent types used in the simulation.

Every agent carries the same six environmental sensors (so every agent can
detect hazards and vote in consensus), but only some can move and each response
type has one special capability.
"""

AGENT_TYPES = {
    "MONITOR_DRONE": {
        "label": "Environmental Monitoring Drone",
        "short": "Monitor drone",
        "prefix": "MD",
        "mobile": True,
        "speed_mps": 30.0,
        "capabilities": ["SENSE", "PATROL", "INVESTIGATE"],
        "action": None,
        "action_rate": 0.0,
        "operating_radius_m": 0.0,
        "description": "Patrols its sector, collects readings, raises alerts and investigates incidents.",
    },
    "FIRE_DRONE": {
        "label": "Fire Response Drone",
        "short": "Fire drone",
        "prefix": "FD",
        "mobile": True,
        "speed_mps": 45.0,
        "capabilities": ["SENSE", "FIRE_SUPPRESSION"],
        "action": "FIRE_SUPPRESSION",
        "action_rate": 0.5,     # severity points removed per tick while on site
        "operating_radius_m": 0.0,
        "description": "Waits at its base, flies to confirmed fires and drops suppressant.",
    },
    "SPRINKLER": {
        "label": "Water Sprinkler Unit",
        "short": "Sprinkler",
        "prefix": "SP",
        "mobile": False,
        "speed_mps": 0.0,
        "capabilities": ["SENSE", "WATER_SPRAY"],
        "action": "WATER_SPRAY",
        "action_rate": 0.35,
        "operating_radius_m": 350.0,
        "description": "Fixed installation. Activates only for fires inside its operating radius.",
    },
    "POLLUTION_UNIT": {
        "label": "Pollution Response Unit",
        "short": "Pollution unit",
        "prefix": "PU",
        "mobile": True,
        "speed_mps": 20.0,
        "capabilities": ["SENSE", "POLLUTION_CLEANUP"],
        "action": "POLLUTION_CLEANUP",
        "action_rate": 0.55,
        "operating_radius_m": 0.0,
        "description": "Ground unit that drives to pollution incidents and runs containment / scrubbing.",
    },
    "COOLING_UNIT": {
        "label": "Cooling / Recovery Unit",
        "short": "Cooling unit",
        "prefix": "CU",
        "mobile": True,
        "speed_mps": 22.0,
        "capabilities": ["SENSE", "COOLING"],
        "action": "COOLING",
        "action_rate": 1.0,
        "operating_radius_m": 0.0,
        "description": "Ground unit that misting-cools areas under extreme heat.",
    },
}

# Fleet composition for a standard 20-agent deployment. The order interleaves
# types so that response units end up spread around the area.
DEFAULT_FLEET_ORDER = [
    "MONITOR_DRONE", "FIRE_DRONE", "MONITOR_DRONE", "SPRINKLER", "POLLUTION_UNIT",
    "MONITOR_DRONE", "FIRE_DRONE", "COOLING_UNIT", "MONITOR_DRONE", "SPRINKLER",
    "POLLUTION_UNIT", "MONITOR_DRONE", "FIRE_DRONE", "MONITOR_DRONE", "SPRINKLER",
    "POLLUTION_UNIT", "FIRE_DRONE", "MONITOR_DRONE", "COOLING_UNIT", "MONITOR_DRONE",
]

# Which capability performs which task type
TASK_TYPE_FOR_CAPABILITY = {
    "INVESTIGATE": "INVESTIGATE",
    "FIRE_SUPPRESSION": "FIRE_SUPPRESSION",
    "WATER_SPRAY": "WATER_SPRAY",
    "POLLUTION_CLEANUP": "POLLUTION_CLEANUP",
    "COOLING": "COOLING",
}
