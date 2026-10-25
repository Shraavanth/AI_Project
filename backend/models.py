"""
Database tables (SQLAlchemy ORM).

The live simulation runs in memory. These tables store what happened so the
History & Analytics page works after a page refresh or a backend restart.
Telemetry and severity are sampled (not written every tick) to keep the
database small.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from backend.database import Base


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DeploymentSite(Base):
    __tablename__ = "deployment_sites"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, index=True, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    radius_m = Column(Float, nullable=False)
    label = Column(String(200), nullable=False)
    source = Column(String(30), nullable=False)       # GEOLOCATION, SEARCH, MAP_PICK, DEMO
    deployed_at = Column(DateTime, default=now, index=True)


class AgentState(Base):
    """Latest known state of every agent (overwritten at each telemetry sample)."""
    __tablename__ = "agent_states"
    agent_id = Column(String(20), primary_key=True)
    run_id = Column(Integer, index=True)
    agent_type = Column(String(30), nullable=False)
    lat = Column(Float)
    lng = Column(Float)
    status = Column(String(20))
    battery = Column(Float)
    health = Column(Float)
    task_id = Column(String(20), nullable=True)
    updated_at = Column(DateTime, default=now)


class TelemetryRecord(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, index=True)
    tick = Column(Integer, index=True)
    agent_id = Column(String(20), index=True)
    agent_type = Column(String(30))
    lat = Column(Float)
    lng = Column(Float)
    status = Column(String(20))
    battery = Column(Float)
    health = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    smoke = Column(Float)
    co2 = Column(Float)
    air_quality = Column(Float)
    soil_moisture = Column(Float)
    ai_status = Column(String(10))
    ai_event = Column(String(20))
    anomaly_score = Column(Float)
    task_id = Column(String(20), nullable=True)
    neighbors = Column(Integer)
    timestamp = Column(DateTime, default=now, index=True)


class IncidentRecord(Base):
    __tablename__ = "incidents"
    incident_id = Column(String(20), primary_key=True)
    run_id = Column(Integer, index=True)
    incident_type = Column(String(20), index=True)
    origin = Column(String(20))
    physical = Column(Boolean, default=True)
    status = Column(String(30), index=True)
    lat = Column(Float)
    lng = Column(Float)
    radius_m = Column(Float)
    initial_severity = Column(Float)
    severity = Column(Float)
    peak_severity = Column(Float)
    estimated_lat = Column(Float, nullable=True)
    estimated_lng = Column(Float, nullable=True)
    coordinator_id = Column(String(20), nullable=True)
    consensus_confidence = Column(Float, nullable=True)
    supporters = Column(Integer, default=0)
    opposers = Column(Integer, default=0)
    detectors_json = Column(Text, default="[]")
    tasks_json = Column(Text, default="[]")
    timeline_json = Column(Text, default="[]")
    rejections = Column(Integer, default=0)
    created_tick = Column(Integer)
    detected_tick = Column(Integer, nullable=True)
    confirmed_tick = Column(Integer, nullable=True)
    response_started_tick = Column(Integer, nullable=True)
    resolved_tick = Column(Integer, nullable=True)
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now, index=True)
    updated_at = Column(DateTime, default=now)


class SeveritySample(Base):
    __tablename__ = "incident_severity"
    id = Column(Integer, primary_key=True)
    incident_id = Column(String(20), index=True)
    tick = Column(Integer)
    severity = Column(Float)
    status = Column(String(30))
    acting_responders = Column(Integer)
    timestamp = Column(DateTime, default=now)


class ConsensusRecord(Base):
    __tablename__ = "consensus_records"
    id = Column(Integer, primary_key=True)
    incident_id = Column(String(20), index=True)
    round = Column(Integer)
    tick = Column(Integer)
    coordinator_id = Column(String(20))
    supporters_json = Column(Text)
    opposers_json = Column(Text)
    abstained_json = Column(Text)
    confidence = Column(Float)
    decision = Column(String(20), index=True)
    votes_json = Column(Text)
    timestamp = Column(DateTime, default=now, index=True)


class TaskRecord(Base):
    __tablename__ = "tasks"
    task_id = Column(String(20), primary_key=True)
    run_id = Column(Integer, index=True)
    incident_id = Column(String(20), index=True)
    task_type = Column(String(30))
    capability = Column(String(30))
    status = Column(String(20), index=True)
    owner_id = Column(String(20), nullable=True)
    previous_owner_id = Column(String(20), nullable=True)
    reassign_count = Column(Integer, default=0)
    work_done = Column(Float, default=0.0)
    owners_json = Column(Text, default="[]")
    created_tick = Column(Integer)
    assigned_tick = Column(Integer, nullable=True)
    started_tick = Column(Integer, nullable=True)
    completed_tick = Column(Integer, nullable=True)
    outcome = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=now)


class TaskEventRecord(Base):
    __tablename__ = "task_events"
    id = Column(Integer, primary_key=True)
    task_id = Column(String(20), index=True)
    incident_id = Column(String(20), index=True)
    task_type = Column(String(30))
    event = Column(String(20), index=True)   # CREATED, ASSIGNED, STARTED, INTERRUPTED, REASSIGNED, UNASSIGNED, COMPLETED, CANCELLED
    from_agent = Column(String(20), nullable=True)
    to_agent = Column(String(20), nullable=True)
    reason = Column(Text)
    tick = Column(Integer)
    timestamp = Column(DateTime, default=now, index=True)


class MessageRecord(Base):
    __tablename__ = "agent_messages"
    id = Column(Integer, primary_key=True)
    message_id = Column(String(20), index=True)
    run_id = Column(Integer, index=True)
    tick = Column(Integer)
    sender = Column(String(20), index=True)
    receiver = Column(String(20), index=True)
    msg_type = Column(String(30), index=True)
    incident_id = Column(String(20), index=True, nullable=True)
    payload_json = Column(Text)
    hops = Column(Integer, nullable=True)
    delivered = Column(Boolean)
    timestamp = Column(DateTime, default=now, index=True)


class AgentFailureRecord(Base):
    __tablename__ = "agent_failures"
    failure_id = Column(String(20), primary_key=True)
    run_id = Column(Integer, index=True)
    agent_id = Column(String(20), index=True)
    agent_type = Column(String(30))
    reason = Column(String(40))
    status_before = Column(String(20))
    task_id = Column(String(20), nullable=True)
    incident_id = Column(String(20), nullable=True)
    failed_tick = Column(Integer)
    detected_tick = Column(Integer, nullable=True)
    detected_by = Column(String(30), nullable=True)
    detection_method = Column(String(30), nullable=True)
    command_center_tick = Column(Integer, nullable=True)
    reassigned_to = Column(String(20), nullable=True)
    reassigned_tick = Column(Integer, nullable=True)
    restored_tick = Column(Integer, nullable=True)
    failed_at = Column(DateTime, default=now, index=True)
    updated_at = Column(DateTime, default=now)


class NetworkEventRecord(Base):
    __tablename__ = "network_events"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, index=True)
    tick = Column(Integer)
    trigger = Column(String(20), index=True)   # FAILURE, RESTORE, AGENT_ADDED, AGENT_REMOVED
    agent_id = Column(String(20), nullable=True)
    links_removed_json = Column(Text)
    links_created_json = Column(Text)
    relay_links_json = Column(Text)
    components_before = Column(Integer)
    components_after = Column(Integer)
    connected_after = Column(Boolean)
    edges_after = Column(Integer)
    operational_agents = Column(Integer)
    compute_ms = Column(Float)
    timestamp = Column(DateTime, default=now, index=True)


class ActivityLogRecord(Base):
    __tablename__ = "activity_log"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, index=True)
    tick = Column(Integer)
    category = Column(String(20), index=True)
    title = Column(String(150))
    message = Column(Text)
    agent_id = Column(String(20), nullable=True, index=True)
    incident_id = Column(String(20), nullable=True, index=True)
    details_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=now, index=True)
