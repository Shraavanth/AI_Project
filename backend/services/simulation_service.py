"""
SimulationService - glue between the FastAPI routes, the simulation engine,
the database and the WebSocket clients.

- One SimulationEngine instance holds the live state (the source of truth).
- A background asyncio task advances it every tick_interval seconds.
  The heavy work (engine.step + database writes) runs in a worker thread so
  the API stays responsive.
- A threading.Lock makes sure an API request and a tick never modify the
  engine at the same time.
- After every tick (and every operator action) the new state is pushed to all
  WebSocket clients.
"""

import asyncio
import json
import os
import threading
from collections import Counter, defaultdict

from sqlalchemy import func

from backend.database import SessionLocal, database_label, init_db
from backend.models import (
    ActivityLogRecord, AgentFailureRecord, ConsensusRecord, DeploymentSite, IncidentRecord,
    MessageRecord, NetworkEventRecord, SeveritySample, TaskEventRecord, TaskRecord, TelemetryRecord,
)
from backend.persistence import PersistenceWriter
from backend.websocket_manager import ws_manager
from simulation import config
from simulation.engine import SimulationEngine
from simulation.environment import OPEN_STATUSES

HISTORY_CATEGORIES = ["SIMULATION", "INCIDENT", "DETECTION", "CONSENSUS", "COORDINATION", "TASK",
                      "RESPONSE", "FAILURE", "RECOVERY", "NETWORK", "AGENT"]


def _loads(text, default):
    try:
        return json.loads(text) if text else default
    except (TypeError, ValueError):
        return default


class SimulationService:

    def __init__(self):
        self.lock = threading.RLock()
        self.persistence = PersistenceWriter()
        self.db_ready = False
        seed = os.getenv("SIM_SEED")
        self.engine = SimulationEngine(seed=int(seed) if seed else None)
        self._loop = None
        self._wake = None
        self._task = None
        self._boot()

    # ==============================================================
    # Startup
    # ==============================================================

    def _boot(self):
        last_site = None
        try:
            init_db()
            self.db_ready = True
            session = SessionLocal()
            try:
                max_run = session.query(func.max(DeploymentSite.run_id)).scalar() or 0
                self.engine.run_id = max_run  # next deploy uses max_run + 1, so ids never collide
                last = session.query(DeploymentSite).order_by(DeploymentSite.id.desc()).first()
                if last:
                    last_site = {"lat": last.lat, "lng": last.lng, "radius_m": last.radius_m,
                                 "label": last.label, "source": last.source}
                # The live simulation is not resumed after a restart; close anything left open.
                session.query(IncidentRecord).filter(IncidentRecord.status.in_(list(OPEN_STATUSES))).update(
                    {"status": "CLOSED_BY_RESTART",
                     "resolution_note": "Backend restarted while the incident was open."}, synchronize_session=False)
                session.query(TaskRecord).filter(TaskRecord.status.in_(["UNASSIGNED", "ASSIGNED", "IN_PROGRESS", "INTERRUPTED"])).update(
                    {"status": "CANCELLED", "outcome": "backend restarted"}, synchronize_session=False)
                session.commit()
            finally:
                session.close()
        except Exception as exc:
            self.persistence.ok = False
            self.persistence.last_error = f"Database unavailable at startup: {exc}"[:300]

        with self.lock:
            if last_site:
                self.engine.deploy(**last_site)
                self.engine.log("SIMULATION", "Backend started",
                                "Backend restarted: a fresh fleet was deployed at the last monitoring area. "
                                "Stored history is still available.")
            else:
                self.engine.deploy(config.DEMO_LATITUDE, config.DEMO_LONGITUDE, config.DEFAULT_RADIUS_M,
                                   config.DEMO_LABEL, "DEMO")
            self._persist_locked()

    # ==============================================================
    # Background loop
    # ==============================================================

    async def start(self):
        self._loop = asyncio.get_running_loop()
        self._wake = asyncio.Event()
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self):
        loop = asyncio.get_running_loop()
        next_tick = loop.time()
        while True:
            try:
                if self.engine.running:
                    if loop.time() >= next_tick:
                        snapshot = await asyncio.to_thread(self._tick)
                        await ws_manager.broadcast("state", snapshot)
                        next_tick = loop.time() + self.engine.tick_interval
                    timeout = max(0.02, next_tick - loop.time())
                else:
                    next_tick = loop.time()
                    timeout = 2.0
                try:
                    await asyncio.wait_for(self._wake.wait(), timeout=timeout)
                    self._wake.clear()
                    snapshot = await asyncio.to_thread(self.snapshot)
                    await ws_manager.broadcast("state", snapshot)
                except asyncio.TimeoutError:
                    if not self.engine.running:
                        await ws_manager.broadcast("state", await asyncio.to_thread(self.snapshot))
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # keep the loop alive whatever happens
                self.engine.log("SIMULATION", "Loop error", f"Simulation loop error: {exc}")
                await asyncio.sleep(1.0)

    def _tick(self):
        with self.lock:
            self.engine.step()
            return self._persist_and_snapshot_locked()

    def notify(self):
        """Ask the loop to push the latest state now (called after operator actions)."""
        if self._loop and self._wake:
            self._loop.call_soon_threadsafe(self._wake.set)

    # ==============================================================
    # Persistence helpers (call with the lock held)
    # ==============================================================

    def _persist_locked(self):
        drained = self.engine.outbox.drain()
        drained["messages"] = self.engine.comms.drain_outbox()
        if self.db_ready:
            self.persistence.flush(self.engine, drained)

    def _persist_and_snapshot_locked(self):
        self._persist_locked()
        return self._snapshot_locked()

    def _snapshot_locked(self):
        data = self.engine.snapshot()
        data["activity"] = [{k: v for k, v in e.items() if k != "details"} for e in data["activity"]]
        data["database"] = {"label": database_label(), **self.persistence.status()}
        data["websocket_clients"] = len(ws_manager.active_connections)
        return data

    def snapshot(self):
        with self.lock:
            return self._snapshot_locked()

    def _action(self, fn, *args, **kwargs):
        """Run an operator action under the lock, persist its records and push an update."""
        with self.lock:
            result = fn(*args, **kwargs)
            self._persist_locked()
        self.notify()
        return result

    # ==============================================================
    # Operator actions
    # ==============================================================

    def deploy(self, lat, lng, radius_m, label, source):
        return self._action(lambda: (self.engine.deploy(lat, lng, radius_m, label, source), self._snapshot_locked())[1])

    def reset(self):
        return self._action(lambda: (self.engine.reset(), self._snapshot_locked())[1])

    def pause(self):
        self._action(self.engine.pause)
        return self.engine.simulation_state()

    def resume(self):
        self._action(self.engine.resume)
        return self.engine.simulation_state()

    def set_speed(self, speed):
        self._action(self.engine.set_speed, speed)
        return self.engine.simulation_state()

    def step_once(self, ticks=1):
        with self.lock:
            for _ in range(ticks):
                self.engine.step()
                self._persist_locked()
            data = self._snapshot_locked()
        self.notify()
        return data

    def create_incident(self, incident_type, lat, lng, radius_m=None, severity=None):
        def run():
            incident = self.engine.create_incident(incident_type, lat, lng, radius_m, severity)
            return self.engine.incident_detail(incident.incident_id)
        return self._action(run)

    def fail_agent(self, agent_id):
        return self._action(lambda: (self.engine.fail_agent(agent_id), self.engine.agent_detail(agent_id))[1])

    def restore_agent(self, agent_id):
        return self._action(lambda: (self.engine.restore_agent(agent_id), self.engine.agent_detail(agent_id))[1])

    def move_agent(self, agent_id, lat, lng):
        return self._action(lambda: (self.engine.move_agent(agent_id, lat, lng), self.engine.agent_detail(agent_id))[1])

    def override_sensors(self, agent_id, readings, duration_ticks):
        return self._action(lambda: (self.engine.override_sensors(agent_id, readings, duration_ticks),
                                     self.engine.agent_detail(agent_id))[1])

    def clear_override(self, agent_id):
        return self._action(lambda: (self.engine.clear_sensor_override(agent_id), self.engine.agent_detail(agent_id))[1])

    def add_agent(self, agent_type, agent_id=None, lat=None, lng=None):
        return self._action(lambda: self.engine.agent_detail(self.engine.add_agent(agent_type, agent_id, lat, lng).agent_id))

    def remove_agent(self, agent_id):
        return self._action(self.engine.remove_agent, agent_id)

    # ==============================================================
    # Live queries
    # ==============================================================

    def status(self):
        with self.lock:
            return {
                "simulation": self.engine.simulation_state(),
                "site": self.engine.site,
                "stats": self.engine.stats(),
                "database": {"label": database_label(), "ready": self.db_ready, **self.persistence.status()},
                "websocket_clients": len(ws_manager.active_connections),
            }

    def agents(self):
        with self.lock:
            return self.engine.agent_dicts()

    def agent_detail(self, agent_id):
        with self.lock:
            return self.engine.agent_detail(agent_id)

    def incidents(self):
        with self.lock:
            return self.engine.incident_dicts()

    def incident_detail(self, incident_id):
        with self.lock:
            return self.engine.incident_detail(incident_id)

    def tasks(self):
        with self.lock:
            return [t.to_dict() for t in reversed(list(self.engine.tasks.values()))]

    def network(self):
        with self.lock:
            return {
                "nodes": [{"id": a.agent_id, "type": a.agent_type, "status": a.status, "lat": round(a.lat, 6),
                           "lng": round(a.lng, 6), "neighbors": len(a.neighbors),
                           "coordinator_of": self.engine.coordinator_roles().get(a.agent_id, [])}
                          for a in self.engine.agents],
                "links": self.engine.network.edges(),
                "connected": self.engine.network.is_connected(),
                "components": self.engine.network.components(),
                "comm_range_m": config.COMM_RANGE_M,
                "max_relay_range_m": config.MAX_RELAY_RANGE_M,
                "events": list(self.engine.network_events),
                "link_churn": self.engine.link_churn,
            }

    def live_messages(self, limit=100, msg_type=None, incident_id=None, agent_id=None):
        with self.lock:
            items = list(self.engine.comms.recent)
        if msg_type:
            items = [m for m in items if m["type"] == msg_type]
        if incident_id:
            items = [m for m in items if m["incident_id"] == incident_id]
        if agent_id:
            items = [m for m in items if agent_id in (m["sender"], m["receiver"])]
        return items[:limit]

    # ==============================================================
    # Stored history (database)
    # ==============================================================

    def _db(self):
        if not self.db_ready:
            raise RuntimeError("Database is unavailable")
        return SessionLocal()

    def history(self, category="ALL", limit=200, incident_id=None, agent_id=None):
        session = self._db()
        try:
            query = session.query(ActivityLogRecord)
            if category and category.upper() != "ALL":
                query = query.filter(ActivityLogRecord.category == category.upper())
            if incident_id:
                query = query.filter(ActivityLogRecord.incident_id == incident_id)
            if agent_id:
                query = query.filter(ActivityLogRecord.agent_id == agent_id)
            rows = query.order_by(ActivityLogRecord.id.desc()).limit(limit).all()
            return [{"id": r.id, "run_id": r.run_id, "tick": r.tick, "category": r.category, "title": r.title,
                     "message": r.message, "agent_id": r.agent_id, "incident_id": r.incident_id,
                     "timestamp": r.timestamp.isoformat() + "Z"} for r in rows]
        finally:
            session.close()

    def stored_messages(self, limit=200, msg_type=None, incident_id=None):
        session = self._db()
        try:
            query = session.query(MessageRecord)
            if msg_type:
                query = query.filter(MessageRecord.msg_type == msg_type)
            if incident_id:
                query = query.filter(MessageRecord.incident_id == incident_id)
            rows = query.order_by(MessageRecord.id.desc()).limit(limit).all()
            return [{"message_id": r.message_id, "run_id": r.run_id, "tick": r.tick, "sender": r.sender,
                     "receiver": r.receiver, "type": r.msg_type, "incident_id": r.incident_id,
                     "payload": _loads(r.payload_json, {}), "hops": r.hops, "delivered": r.delivered,
                     "timestamp": r.timestamp.isoformat() + "Z"} for r in rows]
        finally:
            session.close()

    def stored_incidents(self, limit=100):
        session = self._db()
        try:
            rows = session.query(IncidentRecord).order_by(IncidentRecord.created_at.desc()).limit(limit).all()
            return [self._incident_row(r) for r in rows]
        finally:
            session.close()

    @staticmethod
    def _incident_row(r):
        return {
            "id": r.incident_id, "run_id": r.run_id, "type": r.incident_type, "origin": r.origin,
            "physical": r.physical, "status": r.status, "lat": r.lat, "lng": r.lng, "radius_m": r.radius_m,
            "initial_severity": r.initial_severity, "severity": r.severity, "peak_severity": r.peak_severity,
            "coordinator_id": r.coordinator_id, "consensus_confidence": r.consensus_confidence,
            "supporters": r.supporters, "opposers": r.opposers, "detectors": _loads(r.detectors_json, []),
            "tasks": _loads(r.tasks_json, []), "timeline": _loads(r.timeline_json, []), "rejections": r.rejections,
            "created_tick": r.created_tick, "detected_tick": r.detected_tick, "confirmed_tick": r.confirmed_tick,
            "response_started_tick": r.response_started_tick, "resolved_tick": r.resolved_tick,
            "resolution_note": r.resolution_note, "created_at": r.created_at.isoformat() + "Z",
        }

    def stored_failures(self, limit=100):
        session = self._db()
        try:
            rows = session.query(AgentFailureRecord).order_by(AgentFailureRecord.failed_at.desc()).limit(limit).all()
            return [{c.name: getattr(r, c.name) for c in AgentFailureRecord.__table__.columns} | {
                "failed_at": r.failed_at.isoformat() + "Z", "updated_at": r.updated_at.isoformat() + "Z"} for r in rows]
        finally:
            session.close()

    def stored_task_events(self, limit=200, incident_id=None):
        session = self._db()
        try:
            query = session.query(TaskEventRecord)
            if incident_id:
                query = query.filter(TaskEventRecord.incident_id == incident_id)
            rows = query.order_by(TaskEventRecord.id.desc()).limit(limit).all()
            return [{"task_id": r.task_id, "incident_id": r.incident_id, "task_type": r.task_type, "event": r.event,
                     "from_agent": r.from_agent, "to_agent": r.to_agent, "reason": r.reason, "tick": r.tick,
                     "timestamp": r.timestamp.isoformat() + "Z"} for r in rows]
        finally:
            session.close()

    def stored_network_events(self, limit=50):
        session = self._db()
        try:
            rows = session.query(NetworkEventRecord).order_by(NetworkEventRecord.id.desc()).limit(limit).all()
            return [{"run_id": r.run_id, "tick": r.tick, "trigger": r.trigger, "agent_id": r.agent_id,
                     "links_removed": _loads(r.links_removed_json, []), "links_created": _loads(r.links_created_json, []),
                     "relay_links": _loads(r.relay_links_json, []), "components_before_bridging": r.components_before,
                     "components_after": r.components_after, "connected_after": r.connected_after,
                     "edges_after": r.edges_after, "operational_agents": r.operational_agents,
                     "compute_ms": r.compute_ms, "timestamp": r.timestamp.isoformat() + "Z"} for r in rows]
        finally:
            session.close()

    def stored_consensus(self, incident_id):
        session = self._db()
        try:
            rows = session.query(ConsensusRecord).filter(ConsensusRecord.incident_id == incident_id) \
                .order_by(ConsensusRecord.id.asc()).all()
            return [{"round": r.round, "tick": r.tick, "coordinator_id": r.coordinator_id,
                     "supporters": _loads(r.supporters_json, []), "opposers": _loads(r.opposers_json, []),
                     "abstained": _loads(r.abstained_json, []), "confidence": r.confidence, "decision": r.decision,
                     "timestamp": r.timestamp.isoformat() + "Z"} for r in rows]
        finally:
            session.close()

    def analytics(self):
        """Statistics computed from stored records only (no invented numbers)."""
        session = self._db()
        try:
            run_id = self.engine.run_id
            incidents = session.query(IncidentRecord).all()
            by_type = Counter(r.incident_type for r in incidents)
            by_status = Counter(r.status for r in incidents)

            resolution = []
            for r in incidents:
                if r.status == "RESOLVED" and r.resolved_tick is not None:
                    resolution.append({
                        "incident_id": r.incident_id, "type": r.incident_type, "run_id": r.run_id,
                        "total_s": r.resolved_tick - r.created_tick,
                        "detection_s": (r.detected_tick - r.created_tick) if r.detected_tick is not None else None,
                        "confirmation_s": (r.confirmed_tick - r.detected_tick) if r.confirmed_tick is not None and r.detected_tick is not None else None,
                        "response_start_s": (r.response_started_tick - r.confirmed_tick) if r.response_started_tick is not None and r.confirmed_tick is not None else None,
                        "physical": r.physical,
                    })

            tasks = session.query(TaskRecord).filter(TaskRecord.task_type != "INVESTIGATE").all()
            task_status = Counter(t.status for t in tasks)
            response_durations = []
            for t in tasks:
                if t.status == "COMPLETED" and t.assigned_tick is not None and t.completed_tick is not None:
                    response_durations.append({
                        "task_id": t.task_id, "task_type": t.task_type, "owner_id": t.owner_id,
                        "travel_s": (t.started_tick - t.assigned_tick) if t.started_tick is not None else None,
                        "total_s": t.completed_tick - t.assigned_tick, "reassigned": t.reassign_count > 0,
                    })

            failures = session.query(AgentFailureRecord).all()
            detection_delays = [f.detected_tick - f.failed_tick for f in failures if f.detected_tick is not None]
            reassign_delays = [f.reassigned_tick - f.failed_tick for f in failures if f.reassigned_tick is not None]

            # Environment & availability for the current run, aggregated per sampled tick
            telemetry = session.query(TelemetryRecord.tick, TelemetryRecord.temperature, TelemetryRecord.smoke,
                                      TelemetryRecord.co2, TelemetryRecord.air_quality, TelemetryRecord.ai_status) \
                .filter(TelemetryRecord.run_id == run_id).order_by(TelemetryRecord.tick.desc()).limit(20 * 150).all()
            per_tick = defaultdict(list)
            for row in telemetry:
                per_tick[row.tick].append(row)
            total_agents = len(self.engine.agents)
            environment, availability = [], []
            for tick in sorted(per_tick):
                rows = per_tick[tick]
                n = len(rows)
                environment.append({
                    "tick": tick,
                    "avg_temperature": round(sum(r.temperature for r in rows) / n, 2),
                    "max_temperature": round(max(r.temperature for r in rows), 2),
                    "avg_smoke": round(sum(r.smoke for r in rows) / n, 3),
                    "max_smoke": round(max(r.smoke for r in rows), 3),
                    "avg_co2": round(sum(r.co2 for r in rows) / n, 1),
                    "max_co2": round(max(r.co2 for r in rows), 1),
                    "max_aqi": round(max(r.air_quality for r in rows), 1),
                    "anomalous": sum(1 for r in rows if r.ai_status == "ANOMALY"),
                })
                availability.append({"tick": tick, "operational": n, "offline": max(0, total_agents - n)})

            network_events = session.query(NetworkEventRecord).all()
            message_counts = dict(session.query(MessageRecord.msg_type, func.count(MessageRecord.id))
                                  .group_by(MessageRecord.msg_type).all())

            recent_incidents = [r.incident_id for r in sorted(incidents, key=lambda x: x.created_at, reverse=True)
                                if r.physical][:5]
            severity_series = {}
            for incident_id in recent_incidents:
                samples = session.query(SeveritySample).filter(SeveritySample.incident_id == incident_id) \
                    .order_by(SeveritySample.tick.asc()).all()
                severity_series[incident_id] = [{"tick": s.tick, "severity": s.severity, "acting": s.acting_responders}
                                                for s in samples]

            def avg(values):
                return round(sum(values) / len(values), 2) if values else None

            return {
                "run_id": run_id,
                "incidents": {"total": len(incidents), "by_type": dict(by_type), "by_status": dict(by_status)},
                "resolution_times": sorted(resolution, key=lambda r: r["incident_id"]),
                "average_resolution_s": avg([r["total_s"] for r in resolution]),
                "average_detection_s": avg([r["detection_s"] for r in resolution if r["detection_s"] is not None]),
                "tasks": {"by_status": dict(task_status), "reassigned": sum(1 for t in tasks if t.reassign_count > 0),
                          "total": len(tasks)},
                "response_durations": response_durations[-40:],
                "failures": {
                    "total": len(failures),
                    "by_reason": dict(Counter(f.reason for f in failures)),
                    "by_detection_method": dict(Counter(f.detection_method or "NOT_DETECTED" for f in failures)),
                    "restored": sum(1 for f in failures if f.restored_tick is not None),
                    "reassigned": sum(1 for f in failures if f.reassigned_to),
                    "average_detection_delay_s": avg(detection_delays),
                    "average_reassignment_delay_s": avg(reassign_delays),
                },
                "network": {
                    "reorganizations": len(network_events),
                    "average_compute_ms": avg([n.compute_ms for n in network_events]),
                    "stayed_connected": sum(1 for n in network_events if n.connected_after),
                },
                "messages_by_type": message_counts,
                "environment_series": environment,
                "availability_series": availability,
                "severity_series": severity_series,
            }
        finally:
            session.close()


simulation_service = None


def get_service() -> SimulationService:
    global simulation_service
    if simulation_service is None:
        simulation_service = SimulationService()
    return simulation_service
