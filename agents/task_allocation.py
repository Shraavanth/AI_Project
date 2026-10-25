"""
Capability-based task allocation.

When an incident is confirmed, its coordinator looks at the response plan for
that hazard type (config.RESPONSE_PLAN) and, for every unit needed, chooses one
agent using these rules in order:

    1. Has the required capability
    2. Is operational (not FAILED / RECOVERING)
    3. Is free (no current task)                       -> task load
    4. Has at least MIN_TASK_BATTERY % battery
    5. Can be reached from the coordinator over the network
    6. Fixed units (sprinklers) must already cover the incident with their operating radius

Among the remaining candidates the lowest score wins:

    score = distance_km + (100 - battery) / 100

so the nearest agent is preferred, and a nearly empty battery counts like an
extra kilometre of distance.
"""

from simulation import config


def candidate_report(agent, capability, target, coordinator, network, incident_radius_m, excluded=()):
    """Explain whether an agent can take a task and, if so, its score."""
    lat, lng = target
    distance = agent.distance_to(lat, lng)
    row = {
        "agent_id": agent.agent_id,
        "agent_type": agent.agent_type,
        "distance_m": round(distance),
        "battery": round(agent.battery, 1),
        "eligible": False,
        "score": None,
        "reason": "",
    }
    if agent.agent_id in excluded:
        row["reason"] = "excluded (failed owner)"
    elif not agent.has_capability(capability):
        row["reason"] = f"lacks {capability}"
    elif not agent.operational:
        row["reason"] = f"status {agent.status}"
    elif agent.task_id is not None:
        row["reason"] = f"busy with {agent.task_id}"
    elif agent.battery < config.MIN_TASK_BATTERY:
        row["reason"] = f"battery below {config.MIN_TASK_BATTERY:.0f}%"
    elif coordinator is not None and agent is not coordinator and network.hops(coordinator.agent_id, agent.agent_id) is None:
        if agent.mobile:
            row["eligible"] = True
            row["score"] = round(distance / 1000.0 + 1.5 + (100.0 - agent.battery) / 100.0, 3)
            row["reason"] = "eligible (long-range dispatch across split mesh)"
        else:
            row["reason"] = "unreachable from coordinator"
    elif not agent.mobile and distance > agent.type_info["operating_radius_m"] + incident_radius_m * 0.6:
        row["reason"] = "fixed unit out of operating range"
    else:
        row["eligible"] = True
        row["score"] = round(distance / 1000.0 + (100.0 - agent.battery) / 100.0, 3)
        row["reason"] = "eligible"
    return row


def choose_agent(agents, capability, target, coordinator, network, incident_radius_m, excluded=()):
    """
    Return (best_agent_or_None, candidate_rows) for one task.
    candidate_rows lists every agent that has the capability, with the reason
    it was or was not chosen, so the decision can be shown in the UI.
    """
    rows = []
    best, best_score = None, None
    for agent in agents:
        if not agent.has_capability(capability):
            continue
        row = candidate_report(agent, capability, target, coordinator, network, incident_radius_m, excluded)
        rows.append(row)
        if row["eligible"] and (best_score is None or row["score"] < best_score):
            best, best_score = agent, row["score"]
    rows.sort(key=lambda r: (not r["eligible"], r["score"] if r["score"] is not None else 99, r["distance_m"]))
    return best, rows
