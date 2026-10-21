from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================
# AGENT SCHEMAS
# ============================================================

class AgentCreate(BaseModel):
    id: Optional[str] = None
    x: int = Field(..., ge=0, le=50)
    y: int = Field(..., ge=0, le=50)
    temperature: float = Field(28.0, ge=-20.0, le=100.0)
    humidity: float = Field(60.0, ge=0.0, le=100.0)
    smoke: float = Field(0.10, ge=0.0, le=1.0)
    co2: float = Field(420.0, ge=200.0, le=5000.0)
    air_quality: float = Field(50.0, ge=0.0, le=500.0)
    soil_moisture: float = Field(55.0, ge=0.0, le=100.0)
    battery: int = Field(100, ge=0, le=100)


class AgentUpdate(BaseModel):
    x: Optional[int] = Field(None, ge=0, le=50)
    y: Optional[int] = Field(None, ge=0, le=50)
    temperature: Optional[float] = Field(None, ge=-20.0, le=100.0)
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0)
    smoke: Optional[float] = Field(None, ge=0.0, le=1.0)
    co2: Optional[float] = Field(None, ge=200.0, le=5000.0)
    air_quality: Optional[float] = Field(None, ge=0.0, le=500.0)
    soil_moisture: Optional[float] = Field(None, ge=0.0, le=100.0)
    battery: Optional[int] = Field(None, ge=0, le=100)


class AgentDeploymentRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_km: float = Field(3.0, ge=0.5, le=10.0)
    area_label: str = Field("Selected deployment area", min_length=1, max_length=200)


class AgentDetailResponse(BaseModel):
    id: str
    position: List[int]
    battery: int
    health: int
    connectivity: int
    reliability: int
    status: str
    readings: Dict[str, float]
    neighbors: List[str]
    ai_result: Optional[Dict[str, Any]] = None
    ai_explanation: Optional[Dict[str, Any]] = None
    messages_received: int = 0


# ============================================================
# EVENT TRIGGER SCHEMAS
# ============================================================

class EventTriggerRequest(BaseModel):
    center_x: int = Field(10, ge=0, le=50)
    center_y: int = Field(10, ge=0, le=50)
    radius: int = Field(3, ge=1, le=15)


class EventResponse(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    location: Dict[str, int]
    radius: int
    severity: str
    affected_count: int
    detecting_count: int
    consensus_state: str
    confidence: float
    status: str
    affected_agents: List[str]


# ============================================================
# NETWORK & RECOVERY SCHEMAS
# ============================================================

class NetworkInfoResponse(BaseModel):
    agents_count: int
    connections_count: int
    is_connected: bool
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    last_recovery: Optional[Dict[str, Any]] = None


# ============================================================
# HISTORY & ANALYTICS SCHEMAS
# ============================================================

class AuditLogItem(BaseModel):
    id: int
    category: str
    agent_id: Optional[str] = None
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


class AnalyticsSummaryResponse(BaseModel):
    temperature_trend: List[Dict[str, Any]]
    smoke_trend: List[Dict[str, Any]]
    co2_trend: List[Dict[str, Any]]
    air_quality_trend: List[Dict[str, Any]]
    battery_distribution: List[Dict[str, Any]]
    anomaly_counts_by_event: Dict[str, int]
    active_vs_failed: Dict[str, int]
    recovery_stats: Dict[str, Any]
