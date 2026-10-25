from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from backend.database import Base


# ============================================================
# AGENT RECORD
# ============================================================

class AgentRecord(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(50), unique=True, index=True, nullable=False)
    x = Column(Integer, nullable=False, default=0)
    y = Column(Integer, nullable=False, default=0)
    status = Column(String(20), default="ACTIVE")
    battery = Column(Integer, default=100)
    health = Column(Integer, default=100)
    connectivity = Column(Integer, default=100)
    reliability = Column(Integer, default=100)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentDeploymentRecord(Base):
    __tablename__ = "agent_deployments"

    agent_id = Column(String(50), primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_label = Column(String(200), nullable=False)


class DeploymentSiteRecord(Base):
    __tablename__ = "deployment_site"

    id = Column(Integer, primary_key=True, default=1)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_km = Column(Float, nullable=False)
    area_label = Column(String(200), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# ENVIRONMENTAL READINGS (TELEMETRY HISTORY)
# ============================================================

class EnvironmentalReadingRecord(Base):
    __tablename__ = "environmental_readings"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(50), index=True, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    smoke = Column(Float, nullable=False)
    co2 = Column(Float, nullable=False)
    air_quality = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    ai_status = Column(String(20), default="NORMAL")
    event_classified = Column(String(50), default="None")
    anomaly_score = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# ============================================================
# ENVIRONMENTAL EVENTS / INCIDENTS
# ============================================================

class EnvironmentalEventRecord(Base):
    __tablename__ = "environmental_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, index=True, nullable=False)
    event_type = Column(String(50), nullable=False)  # FIRE, POLLUTION, EXTREME_HEAT, OTHER_ANOMALY
    center_x = Column(Integer, nullable=False)
    center_y = Column(Integer, nullable=False)
    radius = Column(Integer, default=3)
    severity = Column(String(20), default="HIGH")    # LOW, MEDIUM, HIGH, CRITICAL
    affected_count = Column(Integer, default=0)
    detecting_count = Column(Integer, default=0)
    consensus_state = Column(String(50), default="CONFIRMED")
    confidence = Column(Float, default=0.0)
    status = Column(String(20), default="ACTIVE")    # ACTIVE, RESOLVED
    affected_agents_json = Column(Text, default="[]")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# ============================================================
# CONSENSUS DECISION RECORDS
# ============================================================

class ConsensusRecord(Base):
    __tablename__ = "consensus_records"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    consensus_reached = Column(Boolean, default=True)
    confidence = Column(Float, default=0.0)
    total_voters = Column(Integer, default=0)
    agreeing_voters = Column(Integer, default=0)
    evidence_summary = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# ============================================================
# NETWORK REORGANIZATION RECORDS
# ============================================================

class NetworkReorganizationRecord(Base):
    __tablename__ = "network_reorganizations"

    id = Column(Integer, primary_key=True, index=True)
    failed_agent_id = Column(String(50), nullable=False)
    connections_removed = Column(Integer, default=0)
    connections_created = Column(Integer, default=0)
    active_agents_count = Column(Integer, default=0)
    network_connected = Column(Boolean, default=True)
    recovery_time_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# ============================================================
# SYSTEM AUDIT LOGS (TIMELINE)
# ============================================================

class SystemAuditLogRecord(Base):
    __tablename__ = "system_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True, nullable=False)  # EVENT, ANOMALIES, CONSENSUS, FAILURES, RECOVERY, NETWORK, AGENTS
    agent_id = Column(String(50), nullable=True)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    details_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
