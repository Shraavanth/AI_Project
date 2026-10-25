"""
Detection -> alert -> investigation -> consensus -> coordinator -> task allocation.

These functions run inside SimulationEngine.step(). They only use what the
agents can know: their own readings, messages they receive, and the network.
"""

from agents import consensus, self_organization, task_allocation
from agents.agent import COMPLETED, COORDINATING
from agents.agent_types import TASK_TYPE_FOR_CAPABILITY
from simulation import config
from simulation import tasks as T
from simulation.environment import (
    ACTIVE_RESPONSE_STATUSES, CONFIRMED, DETECTED, REJECTED, RESOLVED, UNDETECTED, Incident,
)
from simulation.geo import haversine_m

OPEN_FOR_ALERTS = {UNDETECTED, DETECTED, CONFIRMED, "RESPONDING", "NEEDS_INTERVENTION"}


# ======================================================================
# 6. Detection: persistent local anomalies become alerts
# ======================================================================

def process_detections(engine):
    for agent in engine.agents:
        if not agent.operational or agent.anomaly_streak < config.DETECTION_STREAK_TICKS:
            continue
        if agent.alert_cooldown_until > engine.tick:
            continue
        hazard = agent.streak_event
        incident = _find_incident_for_alert(engine, agent, hazard)

        if incident is None:
            # Nothing known nearby: the agent reports a new incident at its own position.
            incident = Incident(engine._next_incident_id(), hazard, agent.lat, agent.lng,
                                radius_m=300.0, severity=50.0, origin="AGENT_REPORT",
                                tick=engine.tick, physical=False)
            incident.add_timeline(engine.tick, "REPORTED",
                                  f"{agent.agent_id} reported a {hazard} with no known hazard nearby.")
            engine.incidents[incident.incident_id] = incident

        if incident.cooldown_until > engine.tick:
            continue
        if agent.agent_id in incident.detectors and incident.status != UNDETECTED:
            continue

        first_detection = incident.status == UNDETECTED
        if agent.agent_id not in incident.detectors:
            incident.detectors.append(agent.agent_id)

        if first_detection:
            incident.status = DETECTED
            incident.detected_tick = engine.tick
            incident.alert_tick = engine.tick
            incident.no_support_ticks = 0
            incident.last_votes = {}
            incident.investigation_requested = False
            incident.coordinator_id = agent.agent_id
            incident.add_timeline(engine.tick, "DETECTED",
                                  f"{agent.agent_id}'s local AI flagged {hazard} (score {agent.ai_result['score']}). "
                                  f"{agent.agent_id} becomes coordinator (strongest local evidence).")

        update_estimate(engine, incident)
        sent = engine.comms.broadcast_to_neighbors(
            engine.tick, agent, engine.agents_by_id, "INCIDENT_ALERT", incident.incident_id,
            {"hazard": hazard, "score": agent.ai_result["score"],
             "position": [round(agent.lat, 6), round(agent.lng, 6)],
             "readings": {k: round(v, 2) for k, v in agent.readings.items()}})
        for message in sent:
            if message["delivered"]:
                incident.alert_recipients.add(message["receiver"])
        engine.outbox.incidents.add(incident.incident_id)
        engine.log("DETECTION", f"{hazard} detected by {agent.agent_id}",
                   f"{agent.agent_id} saw {hazard} for {agent.anomaly_streak} consecutive readings "
                   f"(anomaly score {agent.ai_result['score']}) and alerted {len(sent)} neighbours.",
                   agent_id=agent.agent_id, incident_id=incident.incident_id)


def _find_incident_for_alert(engine, agent, hazard):
    best, best_d = None, None
    for incident in engine.incidents.values():
        if incident.incident_type != hazard or incident.status not in OPEN_FOR_ALERTS:
            continue
        ref_lat, ref_lng = incident.reference_location()
        d = haversine_m(agent.lat, agent.lng, ref_lat, ref_lng)
        grouping_limit = incident.radius_m + config.GROUPING_EXTRA_M + config.DETECTION_BOUNDARY_TOLERANCE_M
        if d <= grouping_limit and (best_d is None or d < best_d):
            best, best_d = incident, d
    return best


def update_estimate(engine, incident):
    """Estimate the hazard position as the weighted centre of agents currently sensing it."""
    ref_lat, ref_lng = incident.reference_location()
    points = []
    for agent in engine.agents:
        if not agent.operational or agent.ai_result["event"] != incident.incident_type:
            continue
        if haversine_m(agent.lat, agent.lng, ref_lat, ref_lng) > incident.radius_m + config.GROUPING_EXTRA_M:
            continue
        weight = max(0.01, -agent.ai_result["score"]) ** 2
        points.append((agent.lat, agent.lng, weight))
    if points:
        total = sum(w for _, _, w in points)
        incident.estimated_location = (sum(p[0] * p[2] for p in points) / total,
                                       sum(p[1] * p[2] for p in points) / total)


# ======================================================================
# 7. Coordination for every open incident
# ======================================================================

def coordinate_incidents(engine):
    for incident in list(engine.incidents.values()):
        if incident.status in (UNDETECTED, RESOLVED, REJECTED):
            continue
        self_organization.ensure_coordinator(engine, incident)
        update_estimate(engine, incident)
        if incident.status == DETECTED:
            run_consensus(engine, incident)
        if incident.status in ACTIVE_RESPONSE_STATUSES:
            if not incident.response_planned:
                plan_response(engine, incident)
            self_organization.check_task_owners(engine, incident)
            fill_unassigned_tasks(engine, incident)


def _participants(engine, incident):
    ids = set(incident.detectors) | set(incident.alert_recipients)
    for task_id in incident.task_ids:
        task = engine.tasks.get(task_id)
        if task and task.task_type == "INVESTIGATE" and task.owner_id:
            ids.add(task.owner_id)
    return [engine.agents_by_id[i] for i in sorted(ids) if i in engine.agents_by_id]


def run_consensus(engine, incident):
    coordinator = engine.agents_by_id.get(incident.coordinator_id)
    if coordinator is None or not coordinator.operational:
        return
    participants = _participants(engine, incident)
    evidence_point = incident.best_location()
    votes = consensus.collect_votes(incident, participants, coordinator, engine.network, evidence_point)
    in_range = [v for v in votes if v["reason"] != "outside sensing range" and v["vote"] != "ABSTAIN"]

    active_investigators = [
        t for tid in incident.task_ids
        if (t := engine.tasks.get(tid)) and t.task_type == "INVESTIGATE" and t.active and t.owner_id
    ]
    if (not incident.investigation_requested or len(active_investigators) == 0) and len(in_range) < 3:
        request_investigation(engine, incident, coordinator)

    # Evidence messages: each participant reports to the coordinator when its vote changes
    for vote in votes:
        previous = incident.last_votes.get(vote["agent_id"])
        if previous != vote["vote"]:
            incident.last_votes[vote["agent_id"]] = vote["vote"]
            sender = engine.agents_by_id[vote["agent_id"]]
            if sender is not coordinator and sender.operational:
                engine.comms.send(engine.tick, sender, coordinator, "SENSOR_EVIDENCE", incident.incident_id,
                                  {"vote": vote["vote"], "event": vote["ai_event"], "score": vote["score"],
                                   "distance_m": vote["distance_m"], "reason": vote["reason"]})

    result = consensus.evaluate(votes)
    incident.consensus_rounds += 1
    changed = (incident.consensus is None
               or incident.consensus["supporters"] != result["supporters"]
               or incident.consensus["opposers"] != result["opposers"])
    incident.consensus = {**result, "round": incident.consensus_rounds, "tick": engine.tick,
                          "coordinator_id": coordinator.agent_id, "votes": votes,
                          "decision": "PENDING"}
    incident.no_support_ticks = 0 if result["supporters"] else incident.no_support_ticks + 1

    decision = None
    evidence_rounds = engine.tick - incident.alert_tick + 1
    if result["confirmed"] and evidence_rounds >= config.CONSENSUS_MIN_ROUNDS:
        decision = "CONFIRMED"
    elif (engine.tick - incident.alert_tick >= config.CONSENSUS_TIMEOUT_TICKS
          or incident.no_support_ticks >= config.NO_SUPPORT_REJECT_TICKS):
        decision = "REJECTED"

    if changed or decision:
        record = {
            "incident_id": incident.incident_id,
            "round": incident.consensus_rounds,
            "tick": engine.tick,
            "coordinator_id": coordinator.agent_id,
            "supporters": result["supporters"],
            "opposers": result["opposers"],
            "abstained": result["abstained"],
            "confidence": result["confidence"],
            "decision": decision or "PENDING",
            "votes": votes,
        }
        incident.consensus_history.append(record)
        incident.consensus_history = incident.consensus_history[-25:]
        engine.outbox.consensus.append(record)
        engine.outbox.incidents.add(incident.incident_id)

    if decision == "CONFIRMED":
        _confirm(engine, incident, coordinator, participants, result)
    elif decision == "REJECTED":
        _reject(engine, incident, coordinator, participants, result)


def _broadcast_decision(engine, coordinator, participants, incident, decision, result):
    for agent in participants:
        if agent is not coordinator and agent.operational:
            engine.comms.send(engine.tick, coordinator, agent, "CONSENSUS_UPDATE", incident.incident_id,
                              {"decision": decision, "confidence": result["confidence"],
                               "supporters": result["supporters"], "opposers": result["opposers"]})


def _confirm(engine, incident, coordinator, participants, result):
    incident.status = CONFIRMED
    incident.confirmed_tick = engine.tick
    incident.consensus["decision"] = "CONFIRMED"
    _broadcast_decision(engine, coordinator, participants, incident, "CONFIRMED", result)
    incident.add_timeline(engine.tick, "CONFIRMED",
                          f"Local consensus confirmed {incident.incident_type}: {len(result['supporters'])} support, "
                          f"{len(result['opposers'])} oppose, confidence {result['confidence']:.2f}.")
    engine.log("CONSENSUS", f"{incident.incident_type} confirmed",
               f"{incident.incident_id}: {len(result['supporters'])} agents support "
               f"({', '.join(result['supporters'])}), {len(result['opposers'])} oppose. "
               f"Confidence {result['confidence']:.2f} >= {config.CONSENSUS_THRESHOLD}. Coordinator {coordinator.agent_id}.",
               agent_id=coordinator.agent_id, incident_id=incident.incident_id)
    for task_id in incident.task_ids:
        task = engine.tasks.get(task_id)
        if task and task.task_type == "INVESTIGATE" and task.active:
            complete_task(engine, task, "incident confirmed")
    plan_response(engine, incident)


def _reject(engine, incident, coordinator, participants, result):
    incident.consensus["decision"] = "REJECTED"
    incident.rejections += 1
    _broadcast_decision(engine, coordinator, participants, incident, "REJECTED", result)
    for task_id in incident.task_ids:
        task = engine.tasks.get(task_id)
        if task and task.active:
            cancel_task(engine, task, "alert rejected")
    for detector_id in incident.detectors:
        detector = engine.agents_by_id.get(detector_id)
        if detector is not None:
            detector.alert_cooldown_until = engine.tick + 2 * config.DETECTION_COOLDOWN_TICKS
    reason = (f"{len(result['supporters'])} support / {len(result['opposers'])} oppose "
              f"(confidence {result['confidence']:.2f}) - not enough independent evidence.")
    if incident.physical:
        # The hazard still exists in the simulated world; the agents simply could not verify it yet.
        incident.status = UNDETECTED
        incident.detectors = []
        incident.alert_recipients = set()
        incident.coordinator_id = None
        incident.cooldown_until = engine.tick + config.DETECTION_COOLDOWN_TICKS
        incident.add_timeline(engine.tick, "REJECTED", f"Alert rejected: {reason} The hazard is still present and unverified.")
    else:
        incident.status = REJECTED
        incident.resolved_tick = engine.tick
        incident.resolution_note = f"False alarm suppressed by consensus: {reason}"
        incident.add_timeline(engine.tick, "REJECTED", f"False alarm suppressed: {reason}")
    engine.outbox.incidents.add(incident.incident_id)
    engine.log("CONSENSUS", f"Alert rejected ({incident.incident_type})",
               f"{incident.incident_id}: {reason}", agent_id=coordinator.agent_id, incident_id=incident.incident_id)


# ======================================================================
# Investigation
# ======================================================================

def request_investigation(engine, incident, coordinator):
    incident.investigation_requested = True
    target = incident.best_location()
    candidates = []
    max_d = max(config.INVESTIGATION_MAX_DISTANCE_M, (engine.site["radius_m"] * 2.5) if engine.site else 3500.0)
    for agent in engine.agents:
        if not agent.has_capability("INVESTIGATE") or not agent.is_available_for_task():
            continue
        if agent.agent_id in incident.detectors:
            continue
        d = agent.distance_to(*target)
        if d <= config.EVIDENCE_RANGE_M or d > max_d:
            continue
        connected = (coordinator is None or agent is coordinator or engine.network.hops(coordinator.agent_id, agent.agent_id) is not None)
        priority = d if connected else (d + 2000.0)
        candidates.append((priority, agent))
    candidates.sort(key=lambda x: x[0])
    chosen = [a for _, a in candidates[:config.MAX_INVESTIGATORS]]
    for agent in chosen:
        task = T.Task(engine.next_task_id(), incident.incident_id, "INVESTIGATE", "INVESTIGATE", target, engine.tick)
        engine.tasks[task.task_id] = task
        incident.task_ids.append(task.task_id)
        assign_task(engine, task, agent, rows=[], reason="investigate alert")
    if chosen:
        coord_name = coordinator.agent_id if coordinator else "System"
        incident.add_timeline(engine.tick, "INVESTIGATING",
                              f"Too little local evidence; {coord_name} asked {', '.join(a.agent_id for a in chosen)} to investigate.")
    else:
        incident.investigation_requested = False
        incident.add_timeline(engine.tick, "INVESTIGATING", "No monitoring drone currently available to investigate; will retry.")


# ======================================================================
# Task allocation
# ======================================================================

def plan_response(engine, incident):
    incident.response_planned = True
    coordinator = engine.agents_by_id.get(incident.coordinator_id)
    target = incident.best_location()
    created = []
    for capability, count, optional in config.RESPONSE_PLAN[incident.incident_type]:
        for _ in range(count):
            best, rows = task_allocation.choose_agent(engine.agents, capability, target, coordinator,
                                                      engine.network, incident.radius_m)
            if best is None and optional:
                break
            task = T.Task(engine.next_task_id(), incident.incident_id, TASK_TYPE_FOR_CAPABILITY[capability],
                          capability, target, engine.tick, optional=optional)
            engine.tasks[task.task_id] = task
            incident.task_ids.append(task.task_id)
            task.last_decision = rows[:8]
            engine.task_event(task, "CREATED", reason=f"required for {incident.incident_type}")
            if best is not None:
                assign_task(engine, task, best, rows, reason="initial assignment")
            else:
                engine.log("TASK", "No suitable agent",
                           f"{task.task_id} ({capability}) for {incident.incident_id} has no eligible agent right now; "
                           "it will be assigned as soon as one becomes available.",
                           incident_id=incident.incident_id)
            created.append(task)
    summary = ", ".join(f"{t.task_type}->{t.owner_id or 'UNASSIGNED'}" for t in created)
    incident.add_timeline(engine.tick, "TASKS_ASSIGNED", f"Coordinator {incident.coordinator_id} planned: {summary}.")
    engine.outbox.incidents.add(incident.incident_id)


def assign_task(engine, task, agent, rows, reason, reassigned_from=None):
    incident = engine.incidents[task.incident_id]
    coordinator = engine.agents_by_id.get(incident.coordinator_id)
    chosen_row = next((r for r in rows if r["agent_id"] == agent.agent_id), None)
    payload = {"task_id": task.task_id, "task_type": task.task_type,
               "target": [round(task.target[0], 6), round(task.target[1], 6)],
               "score": chosen_row["score"] if chosen_row else None, "reason": reason}

    if coordinator is not None and coordinator is not agent:
        engine.comms.send(engine.tick, coordinator, agent, "TASK_PROPOSAL", incident.incident_id, payload)
        engine.comms.send(engine.tick, agent, coordinator, "TASK_ACCEPTED", incident.incident_id,
                          {"task_id": task.task_id, "battery": round(agent.battery, 1),
                           "distance_m": round(agent.distance_to(*task.target))})

    task.owner_id = agent.agent_id
    task.status = T.ASSIGNED
    task.assigned_tick = engine.tick
    task.unassigned_since = None
    task.owner_missing_ticks = 0
    task.started_tick = None if task.task_type != "INVESTIGATE" else task.started_tick
    task.arrived_tick = None
    task.start_distance_m = None
    task.travel_progress = 0.0
    if rows:
        task.last_decision = rows[:8]
    task.owners.append({"agent_id": agent.agent_id, "from_tick": engine.tick, "to_tick": None, "end": None})

    agent.task_id = task.task_id
    agent.destination = task.target
    agent.destination_label = f"{task.task_type} at {incident.incident_id}"
    agent.manual_hold_until = None
    agent.charge_mode = False
    agent.hold(COORDINATING, engine.tick)
    agent.task_history.append({"task_id": task.task_id, "incident_id": incident.incident_id,
                               "task_type": task.task_type, "assigned_tick": engine.tick,
                               "reassigned_from": reassigned_from, "ended_tick": None, "outcome": None})

    if reassigned_from:
        task.reassign_count += 1
        engine.task_event(task, "REASSIGNED", from_agent=reassigned_from, to_agent=agent.agent_id, reason=reason)
        if coordinator is not None:
            engine.comms.broadcast_to_neighbors(engine.tick, coordinator, engine.agents_by_id, "TASK_REASSIGNED",
                                                incident.incident_id,
                                                {"task_id": task.task_id, "from": reassigned_from, "to": agent.agent_id})
            if agent.agent_id not in coordinator.neighbors and agent is not coordinator:
                engine.comms.send(engine.tick, coordinator, agent, "TASK_REASSIGNED", incident.incident_id,
                                  {"task_id": task.task_id, "from": reassigned_from, "to": agent.agent_id})
        incident.add_timeline(engine.tick, "REASSIGNED",
                              f"{task.task_type} task {task.task_id} reassigned from {reassigned_from} to {agent.agent_id}.")
        engine.log("TASK", f"Task reassigned to {agent.agent_id}",
                   f"{task.task_id} ({task.task_type}) moved from {reassigned_from} to {agent.agent_id} "
                   f"({chosen_row['distance_m'] if chosen_row else '?'} m away, battery {agent.battery:.0f}%).",
                   agent_id=agent.agent_id, incident_id=incident.incident_id)
    else:
        engine.task_event(task, "ASSIGNED", to_agent=agent.agent_id, reason=reason)
        if task.task_type != "INVESTIGATE":
            engine.log("TASK", f"{task.task_type.replace('_', ' ').title()} assigned",
                       f"{task.task_id}: {agent.agent_id} selected for {task.task_type.lower().replace('_', ' ')} "
                       f"at {incident.incident_id} ({chosen_row['distance_m'] if chosen_row else '?'} m, "
                       f"battery {agent.battery:.0f}%).", agent_id=agent.agent_id, incident_id=incident.incident_id)
        else:
            engine.log("TASK", "Investigation requested",
                       f"{agent.agent_id} sent to investigate {incident.incident_id}.",
                       agent_id=agent.agent_id, incident_id=incident.incident_id)
    engine.outbox.incidents.add(incident.incident_id)


def fill_unassigned_tasks(engine, incident):
    coordinator = engine.agents_by_id.get(incident.coordinator_id)
    for task_id in incident.task_ids:
        task = engine.tasks.get(task_id)
        if task is None or task.status != T.UNASSIGNED:
            continue
        # Failed agents are already ineligible, so no extra exclusion is needed here
        # (a restored former owner may legitimately take its task back).
        best, rows = task_allocation.choose_agent(engine.agents, task.capability, incident.best_location(),
                                                  coordinator, engine.network, incident.radius_m)
        task.last_decision = rows[:8]
        if best is not None:
            assign_task(engine, task, best, rows, reason="agent became available",
                        reassigned_from=task.previous_owner_id)


def _release_owner(engine, task, outcome):
    agent = engine.agents_by_id.get(task.owner_id)
    if agent is not None and agent.task_id == task.task_id:
        agent.task_id = None
        agent.destination = None
        agent.destination_label = None
        for entry in reversed(agent.task_history):
            if entry["task_id"] == task.task_id and entry["outcome"] is None:
                entry["outcome"] = outcome
                entry["ended_tick"] = engine.tick
                break
    return agent


def complete_task(engine, task, note):
    incident = engine.incidents.get(task.incident_id)
    task.status = T.COMPLETED
    task.completed_tick = engine.tick
    task.outcome = note
    task.end_current_owner(engine.tick, "COMPLETED")
    agent = _release_owner(engine, task, "COMPLETED")
    engine.task_event(task, "COMPLETED", from_agent=task.owner_id, reason=note)
    if agent is not None and agent.operational:
        agent.hold(COMPLETED, engine.tick + config.COMPLETED_HOLD_TICKS)
        coordinator = engine.agents_by_id.get(incident.coordinator_id) if incident else None
        if coordinator and coordinator is not agent:
            engine.comms.send(engine.tick, agent, coordinator, "TASK_COMPLETED", task.incident_id,
                              {"task_id": task.task_id, "work_done": round(task.work_done, 1), "note": note})


def cancel_task(engine, task, note):
    task.status = T.CANCELLED
    task.completed_tick = engine.tick
    task.outcome = note
    task.end_current_owner(engine.tick, "CANCELLED")
    _release_owner(engine, task, "CANCELLED")
    engine.task_event(task, "CANCELLED", from_agent=task.owner_id, reason=note)


def resolve_incident(engine, incident, note):
    incident.status = RESOLVED
    incident.resolved_tick = engine.tick
    incident.resolution_note = note
    for task_id in incident.task_ids:
        task = engine.tasks.get(task_id)
        if task is None or not task.active:
            continue
        if task.status in (T.ASSIGNED, T.IN_PROGRESS) and task.owner_id:
            complete_task(engine, task, "incident resolved")
        else:
            cancel_task(engine, task, "incident resolved")
    engine.resolved_count += 1
    duration = engine.tick - incident.created_tick
    incident.add_timeline(engine.tick, "RESOLVED", f"{note} Total time {duration} s.")
    engine.outbox.incidents.add(incident.incident_id)
    engine.log("INCIDENT", f"{incident.incident_type} resolved",
               f"{incident.incident_id} resolved after {duration} s. {note}", incident_id=incident.incident_id)
