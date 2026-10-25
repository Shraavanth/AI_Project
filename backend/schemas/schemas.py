"""Request bodies (validated by Pydantic -> invalid input returns HTTP 422)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from simulation import config

AgentTypeName = Literal["MONITOR_DRONE", "FIRE_DRONE", "SPRINKLER", "POLLUTION_UNIT", "COOLING_UNIT"]
IncidentTypeName = Literal["FIRE", "POLLUTION", "EXTREME_HEAT"]
LocationSource = Literal["GEOLOCATION", "SEARCH", "MAP_PICK", "DEMO", "MANUAL"]


class DeployRequest(BaseModel):
    latitude: float = Field(..., ge=-85.0, le=85.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_m: float = Field(config.DEFAULT_RADIUS_M, ge=config.MIN_RADIUS_M, le=config.MAX_RADIUS_M)
    label: str = Field("Monitoring area", min_length=1, max_length=120)
    source: LocationSource = "MANUAL"


class SpeedRequest(BaseModel):
    speed: float


class StepRequest(BaseModel):
    ticks: int = Field(1, ge=1, le=600)


class IncidentCreate(BaseModel):
    type: IncidentTypeName
    latitude: float = Field(..., ge=-85.0, le=85.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_m: Optional[float] = Field(None, ge=100, le=1500)
    severity: Optional[float] = Field(None, ge=10, le=100)


class MoveRequest(BaseModel):
    latitude: float = Field(..., ge=-85.0, le=85.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class SensorOverride(BaseModel):
    temperature: Optional[float] = Field(None, ge=-30.0, le=90.0)
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0)
    smoke: Optional[float] = Field(None, ge=0.0, le=1.0)
    co2: Optional[float] = Field(None, ge=250.0, le=5000.0)
    air_quality: Optional[float] = Field(None, ge=0.0, le=500.0)
    soil_moisture: Optional[float] = Field(None, ge=0.0, le=100.0)
    duration_ticks: int = Field(20, ge=1, le=300)


class AgentCreate(BaseModel):
    agent_type: AgentTypeName
    agent_id: Optional[str] = Field(None, min_length=2, max_length=12, pattern=r"^[A-Za-z0-9\-_]+$")
    latitude: Optional[float] = Field(None, ge=-85.0, le=85.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
