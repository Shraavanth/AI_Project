"""
Writes the records produced by the simulation to the database.

The simulation keeps running even if the database is unavailable: errors are
caught, counted and reported through /api/status instead of crashing the loop.
"""

import json
from datetime import datetime

from sqlalchemy import func

from backend.database import SessionLocal
from backend.models import (
    ActivityLogRecord, AgentFailureRecord, AgentState, ConsensusRecord, DeploymentSite,
    IncidentRecord, MessageRecord, NetworkEventRecord, SeveritySample, TaskEventRecord,
    TaskRecord, TelemetryRecord, now,
)
from simulation import config


def _ts(value):
    if not value:
        return now()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return now()


def _dumps(value):
    return json.dumps(value, default=str)


class PersistenceWriter:

    def __init__(self):
        self.ok = True
        self.last_error = None
        self.errors = 0
        self.writes = 0
        self._telemetry_writes = 0

    def status(self) -> dict:
        return {"ok": self.ok, "last_error": self.last_error, "errors": self.errors, "flushes": self.writes}

    def flush(self, engine, drained: dict):
        """Persist one drained outbox. engine is used to read current incident/task state."""
        if not any([drained["activity"], drained["consensus"], drained["task_events"], drained["failures"],
                    drained["network_events"], drained["severity"], drained["telemetry"], drained["incidents"],
                    drained["tasks"], drained["site"], drained.get("messages")]):
            return
        run_id = engine.run_id
        session = SessionLocal()
        try:
            if drained["site"]:
                site = drained["site"]
                session.add(DeploymentSite(run_id=run_id, lat=site["lat"], lng=site["lng"], radius_m=site["radius_m"],
                                           label=site["label"], source=site["source"], deployed_at=_ts(site["deployed_at"])))

            for e in drained["activity"]:
                session.add(ActivityLogRecord(run_id=run_id, tick=e["tick"], category=e["category"], title=e["title"][:150],
                                              message=e["message"], agent_id=e["agent_id"], incident_id=e["incident_id"],
                                              details_json=_dumps(e["details"]), timestamp=_ts(e["timestamp"])))

            for m in drained.get("messages", []):
                session.add(MessageRecord(message_id=m["message_id"], run_id=run_id, tick=m["tick"], sender=m["sender"],
                                          receiver=m["receiver"], msg_type=m["type"], incident_id=m["incident_id"],
                                          payload_json=_dumps(m["payload"]), hops=m["hops"], delivered=m["delivered"],
                                          timestamp=_ts(m["timestamp"])))

            for c in drained["consensus"]:
                session.add(ConsensusRecord(incident_id=c["incident_id"], round=c["round"], tick=c["tick"],
                                            coordinator_id=c["coordinator_id"], supporters_json=_dumps(c["supporters"]),
                                            opposers_json=_dumps(c["opposers"]), abstained_json=_dumps(c["abstained"]),
                                            confidence=c["confidence"], decision=c["decision"], votes_json=_dumps(c["votes"])))

            for t in drained["task_events"]:
                session.add(TaskEventRecord(task_id=t["task_id"], incident_id=t["incident_id"], task_type=t["task_type"],
                                            event=t["event"], from_agent=t["from_agent"], to_agent=t["to_agent"],
                                            reason=t["reason"], tick=t["tick"], timestamp=_ts(t["timestamp"])))

            for n in drained["network_events"]:
                session.add(NetworkEventRecord(run_id=run_id, tick=n["tick"], trigger=n["trigger"], agent_id=n["agent_id"],
                                               links_removed_json=_dumps(n["links_removed"]),
                                               links_created_json=_dumps(n["links_created"]),
                                               relay_links_json=_dumps(n["relay_links"]),
                                               components_before=n["components_before_bridging"],
                                               components_after=n["components_after"], connected_after=n["connected_after"],
                                               edges_after=n["edges_after"], operational_agents=n["operational_agents"],
                                               compute_ms=n["compute_ms"], timestamp=_ts(n["timestamp"])))

            for s in drained["severity"]:
                session.add(SeveritySample(incident_id=s["incident_id"], tick=s["tick"], severity=s["severity"],
                                           status=s["status"], acting_responders=s["acting_responders"],
                                           timestamp=_ts(s["timestamp"])))

            for f in drained["failures"]:
                session.merge(AgentFailureRecord(
                    failure_id=f["failure_id"], run_id=run_id, agent_id=f["agent_id"], agent_type=f["agent_type"],
                    reason=f["reason"], status_before=f["status_before"], task_id=f["task_id"], incident_id=f["incident_id"],
                    failed_tick=f["failed_tick"], detected_tick=f["detected_tick"], detected_by=f["detected_by"],
                    detection_method=f["detection_method"], command_center_tick=f["command_center_tick"],
                    reassigned_to=f["reassigned_to"], reassigned_tick=f["reassigned_tick"],
                    restored_tick=f["restored_tick"], failed_at=_ts(f["failed_at"]), updated_at=now()))

            for incident_id in drained["incidents"]:
                incident = engine.incidents.get(incident_id)
                if incident is None:
                    continue
                tasks = [engine.tasks[t] for t in incident.task_ids if t in engine.tasks]
                cons = incident.consensus or {}
                est = incident.estimated_location
                session.merge(IncidentRecord(
                    incident_id=incident.incident_id, run_id=run_id, incident_type=incident.incident_type,
                    origin=incident.origin, physical=incident.physical, status=incident.status,
                    lat=incident.lat, lng=incident.lng, radius_m=incident.radius_m,
                    initial_severity=incident.initial_severity, severity=round(incident.severity, 2),
                    peak_severity=round(incident.peak_severity, 2),
                    estimated_lat=est[0] if est else None, estimated_lng=est[1] if est else None,
                    coordinator_id=incident.coordinator_id, consensus_confidence=cons.get("confidence"),
                    supporters=len(cons.get("supporters", [])), opposers=len(cons.get("opposers", [])),
                    detectors_json=_dumps(incident.detectors), tasks_json=_dumps([t.to_summary() for t in tasks]),
                    timeline_json=_dumps(incident.timeline), rejections=incident.rejections,
                    created_tick=incident.created_tick, detected_tick=incident.detected_tick,
                    confirmed_tick=incident.confirmed_tick, response_started_tick=incident.response_started_tick,
                    resolved_tick=incident.resolved_tick, resolution_note=incident.resolution_note, updated_at=now()))

            for task_id in drained["tasks"]:
                task = engine.tasks.get(task_id)
                if task is None:
                    continue
                session.merge(TaskRecord(
                    task_id=task.task_id, run_id=run_id, incident_id=task.incident_id, task_type=task.task_type,
                    capability=task.capability, status=task.status, owner_id=task.owner_id,
                    previous_owner_id=task.previous_owner_id, reassign_count=task.reassign_count,
                    work_done=round(task.work_done, 2), owners_json=_dumps(task.owners),
                    created_tick=task.created_tick, assigned_tick=task.assigned_tick, started_tick=task.started_tick,
                    completed_tick=task.completed_tick, outcome=task.outcome, updated_at=now()))

            if drained["telemetry"]:
                for r in drained["telemetry"]:
                    session.add(TelemetryRecord(run_id=run_id, timestamp=_ts(r.pop("timestamp")), **r))
                for agent in engine.agents:
                    session.merge(AgentState(agent_id=agent.agent_id, run_id=run_id, agent_type=agent.agent_type,
                                             lat=round(agent.lat, 6), lng=round(agent.lng, 6), status=agent.status,
                                             battery=round(agent.battery, 1), health=round(agent.health, 1),
                                             task_id=agent.task_id, updated_at=now()))
                self._telemetry_writes += 1

            session.commit()
            self.writes += 1
            self.ok = True

            if self._telemetry_writes and self._telemetry_writes % 50 == 0:
                self._prune_telemetry()
        except Exception as exc:  # database down, locked, misconfigured...
            session.rollback()
            self.ok = False
            self.errors += 1
            self.last_error = str(exc)[:300]
        finally:
            session.close()

    def _prune_telemetry(self):
        session = SessionLocal()
        try:
            total = session.query(func.count(TelemetryRecord.id)).scalar() or 0
            excess = total - config.MAX_TELEMETRY_ROWS
            if excess > 0:
                cutoff = session.query(TelemetryRecord.id).order_by(TelemetryRecord.id.asc()).offset(excess).limit(1).scalar()
                if cutoff:
                    session.query(TelemetryRecord).filter(TelemetryRecord.id < cutoff).delete(synchronize_session=False)
                    session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
