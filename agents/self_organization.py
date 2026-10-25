"""
Failure detection, coordinator re-election and task reassignment.

How a failure is discovered (no agent can "see" another agent's status directly):

1. Peer heartbeat  - linked neighbours hear each other every tick. If agent A
                     has not heard neighbour B for HEARTBEAT_TIMEOUT_TICKS and
                     there is no longer any route to B through the mesh, A
                     declares B lost and sends FAILURE_ALERT to its neighbours.
                     (If B is still reachable through other agents it simply
                     moved out of direct range, so nothing is reported.)
2. Task owner check - every incident coordinator keeps track of its task owners.
                     If an owner cannot be reached for HEARTBEAT_TIMEOUT_TICKS,
                     the coordinator interrupts the task and reassigns it.
3. Command Center   - receives telemetry from every operational agent each tick.
                     After TELEMETRY_TIMEOUT_TICKS of silence it marks the agent
                     offline (monitoring only - the Command Center does not give
                     orders; recovery is decided by the agents themselves).
"""

from agents import task_allocation
from simulation import config
from simulation import tasks as T


def _mark_detected(engine, agent_id, detected_by, method):
    failure_id = engine.open_failure_by_agent.get(agent_id)
    if not failure_id:
        return None
    failure = engine.failures[failure_id]
    if failure["detected_tick"] is None:
        failure["detected_tick"] = engine.tick
        failure["detected_by"] = detected_by
        failure["detection_method"] = method
        engine.outbox.failures[failure_id] = failure
    return failure


def detect_lost_neighbors(engine):
    for agent in engine.agents:
        if not agent.operational:
            continue
        for neighbor_id, last_tick in list(agent.last_heard.items()):
            if engine.tick - last_tick < config.HEARTBEAT_TIMEOUT_TICKS:
                continue
            del agent.last_heard[neighbor_id]
            if engine.network.hops(agent.agent_id, neighbor_id) is not None:
                continue  # still reachable through the mesh: it just moved out of direct range
            lost = engine.agents_by_id.get(neighbor_id)
            if lost is None:
                continue
            failure = _mark_detected(engine, neighbor_id, agent.agent_id, "PEER_HEARTBEAT")
            first = failure is not None and failure["detected_by"] == agent.agent_id and failure["detected_tick"] == engine.tick
            sent = engine.comms.broadcast_to_neighbors(
                engine.tick, agent, engine.agents_by_id, "FAILURE_ALERT",
                failure["incident_id"] if failure else None,
                {"lost_agent": neighbor_id, "last_heard_tick": last_tick,
                 "silent_for": engine.tick - last_tick})
            if first:
                engine.log("FAILURE", f"Failure detected: {neighbor_id}",
                           f"{agent.agent_id} heard nothing from {neighbor_id} for {engine.tick - last_tick} s and has "
                           f"no route to it. FAILURE_ALERT sent to {len(sent)} neighbours.",
                           agent_id=neighbor_id, incident_id=failure["incident_id"])


def check_command_center_telemetry(engine):
    for agent in engine.agents:
        failure_id = engine.open_failure_by_agent.get(agent.agent_id)
        if not failure_id or agent.last_telemetry_tick is None:
            continue
        failure = engine.failures[failure_id]
        if failure["command_center_tick"] is None and engine.tick - agent.last_telemetry_tick >= config.TELEMETRY_TIMEOUT_TICKS:
            failure["command_center_tick"] = engine.tick
            if failure["detected_tick"] is None:
                failure["detected_tick"] = engine.tick
                failure["detected_by"] = "COMMAND_CENTER"
                failure["detection_method"] = "TELEMETRY_TIMEOUT"
            engine.outbox.failures[failure_id] = failure
            engine.log("FAILURE", f"Telemetry lost: {agent.agent_id}",
                       f"Command Center has received no telemetry from {agent.agent_id} for "
                       f"{engine.tick - agent.last_telemetry_tick} s - marked offline.", agent_id=agent.agent_id)


def ensure_coordinator(engine, incident):
    """Re-elect a coordinator if the current one failed."""
    current = engine.agents_by_id.get(incident.coordinator_id)
    if current is not None and current.operational:
        return current

    target = incident.best_location()
    involved = set(incident.detectors) | set(incident.alert_recipients)
    for task_id in incident.task_ids:
        task = engine.tasks.get(task_id)
        if task and task.owner_id:
            involved.add(task.owner_id)
    pool = [engine.agents_by_id[i] for i in involved if i in engine.agents_by_id and engine.agents_by_id[i].operational]
    if not pool:
        pool = [a for a in engine.agents if a.operational and a.distance_to(*target) <= 1500]
    if not pool:
        pool = [a for a in engine.agents if a.operational]
    if not pool:
        return None

    # Nearest to the incident, with battery as a tie-breaker
    new = min(pool, key=lambda a: (round(a.distance_to(*target) / 100), -a.battery))
    old_id = incident.coordinator_id
    incident.coordinator_id = new.agent_id
    engine.comms.broadcast_to_neighbors(engine.tick, new, engine.agents_by_id, "COORDINATOR_CHANGE",
                                        incident.incident_id, {"old": old_id, "new": new.agent_id})
    incident.add_timeline(engine.tick, "COORDINATOR",
                          f"Coordinator {old_id or '-'} unavailable; {new.agent_id} took over coordination.")
    engine.outbox.incidents.add(incident.incident_id)
    engine.log("COORDINATION", f"New coordinator: {new.agent_id}",
               f"{incident.incident_id}: {old_id or 'no coordinator'} is unavailable, {new.agent_id} "
               f"(nearest involved agent) now coordinates.", agent_id=new.agent_id, incident_id=incident.incident_id)
    return new


def check_task_owners(engine, incident):
    """Interrupt and reassign tasks whose owner can no longer be reached."""
    from simulation import coordination  # local import avoids a circular import

    coordinator = engine.agents_by_id.get(incident.coordinator_id)
    for task_id in list(incident.task_ids):
        task = engine.tasks.get(task_id)
        if task is None or task.status not in (T.ASSIGNED, T.IN_PROGRESS, T.INTERRUPTED) or not task.owner_id:
            continue
        owner = engine.agents_by_id.get(task.owner_id)
        reachable = (owner is not None and owner.operational and
                     (coordinator is None or owner is coordinator or
                      engine.network.hops(coordinator.agent_id, owner.agent_id) is not None))
        task.owner_missing_ticks = 0 if reachable else task.owner_missing_ticks + 1
        if task.owner_missing_ticks < config.HEARTBEAT_TIMEOUT_TICKS:
            continue

        lost_id = task.owner_id
        if task.status != T.INTERRUPTED:
            task.status = T.INTERRUPTED
            task.interrupted_tick = engine.tick
            engine.task_event(task, "INTERRUPTED", from_agent=lost_id, reason="owner unreachable")

        if coordinator is not None:
            engine.comms.broadcast_to_neighbors(engine.tick, coordinator, engine.agents_by_id, "FAILURE_ALERT",
                                                incident.incident_id,
                                                {"lost_agent": lost_id, "task_id": task.task_id,
                                                 "silent_for": task.owner_missing_ticks})
        failure = _mark_detected(engine, lost_id, coordinator.agent_id if coordinator else "COORDINATOR", "TASK_OWNER_TIMEOUT")

        # Remove ownership from the lost agent (if it is alive but cut off, it stops too)
        task.end_current_owner(engine.tick, "INTERRUPTED")
        if owner is not None and owner.task_id == task.task_id:
            owner.task_id = None
            owner.destination = None
            for entry in reversed(owner.task_history):
                if entry["task_id"] == task.task_id and entry["outcome"] is None:
                    entry["outcome"] = "INTERRUPTED"
                    entry["ended_tick"] = engine.tick
                    break
        task.previous_owner_id = lost_id
        task.owner_id = None
        task.owner_missing_ticks = 0

        if task.task_type == "INVESTIGATE":
            best, rows = task_allocation.choose_agent(engine.agents, "INVESTIGATE", incident.best_location(),
                                                      coordinator, engine.network, incident.radius_m, excluded={lost_id})
            task.last_decision = rows[:8]
            if best is not None:
                coordination.assign_task(engine, task, best, rows, reason=f"replacing failed investigator {lost_id}",
                                         reassigned_from=lost_id)
                if failure is not None:
                    failure["reassigned_to"] = best.agent_id
                    failure["reassigned_tick"] = engine.tick
                    engine.outbox.failures[failure["failure_id"]] = failure
                incident.add_timeline(engine.tick, "INVESTIGATING",
                                      f"Investigator {lost_id} failed; {best.agent_id} reassigned to investigate {incident.incident_id}.")
            else:
                incident.investigation_requested = False
                coordination.cancel_task(engine, task, f"investigator {lost_id} lost and no immediate replacement available")
            continue

        best, rows = task_allocation.choose_agent(engine.agents, task.capability, incident.best_location(),
                                                  coordinator, engine.network, incident.radius_m, excluded={lost_id})
        task.last_decision = rows[:8]
        if best is not None:
            coordination.assign_task(engine, task, best, rows, reason=f"replacing failed {lost_id}",
                                     reassigned_from=lost_id)
            if failure is not None:
                failure["reassigned_to"] = best.agent_id
                failure["reassigned_tick"] = engine.tick
                engine.outbox.failures[failure["failure_id"]] = failure
        elif task.optional:
            coordination.cancel_task(engine, task, f"optional unit {lost_id} lost; no other unit in range")
            incident.add_timeline(engine.tick, "TASK_CANCELLED",
                                  f"Optional {task.task_type} task {task.task_id} cancelled - {lost_id} failed and no other unit covers the area.")
        else:
            task.status = T.UNASSIGNED
            task.unassigned_since = engine.tick
            engine.task_event(task, "UNASSIGNED", from_agent=lost_id, reason="no suitable replacement")
            incident.add_timeline(engine.tick, "NO_REPLACEMENT",
                                  f"{task.task_type} task {task.task_id} lost its owner {lost_id}; no suitable replacement available.")
            engine.log("TASK", "No replacement available",
                       f"{task.task_id} ({task.task_type}) lost {lost_id} and no capable agent is free and reachable. "
                       "Task stays UNASSIGNED until one becomes available.",
                       incident_id=incident.incident_id)
