from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator

def now_iso(): return datetime.now(timezone.utc).isoformat()

class Position(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    captured_at: datetime

class Telemetry(BaseModel):
    connected: bool = True
    position: Position
    heading_deg: float = Field(ge=0, lt=360)
    speed_mps: float = Field(ge=0, le=30)
    front_distance_cm: float = Field(ge=0, le=100000)
    battery_percent: float = Field(ge=0, le=100)
    packet_loss_percent: float = Field(ge=0, le=100)
    heartbeat_at: datetime

    @field_validator("heartbeat_at", "position")
    @classmethod
    def validate_time(cls, value): return value

class RouteSelection(BaseModel):
    route_id: str = Field(pattern="^[AB]$")

def default_telemetry():
    t = now_iso()
    return Telemetry(position=Position(latitude=3.5952, longitude=98.6722, captured_at=t), heading_deg=32, speed_mps=0, front_distance_cm=600, battery_percent=92, packet_loss_percent=0, heartbeat_at=t)
