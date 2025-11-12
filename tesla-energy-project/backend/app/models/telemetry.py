from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    LOW_BATTERY = "low_battery"
    GRID_OUTAGE = "grid_outage"
    HIGH_TEMPERATURE = "high_temperature"
    LOW_TEMPERATURE = "low_temperature"
    CHARGE_LIMIT = "charge_limit"
    DISCHARGE_LIMIT = "discharge_limit"
    FIRMWARE_UPDATE = "firmware_update"
    SYSTEM_FAULT = "system_fault"


class Telemetry(BaseModel):
    device_id: str
    timestamp: datetime
    battery_charge_percent: float = Field(ge=0.0, le=100.0)
    battery_power_kw: float  # Positive = charging, Negative = discharging
    solar_power_kw: float = Field(ge=0.0)
    grid_power_kw: float  # Positive = drawing from grid, Negative = exporting to grid
    home_power_kw: float  # Total home consumption
    battery_temperature_c: float
    inverter_temperature_c: Optional[float] = None
    voltage: Optional[float] = None
    frequency_hz: Optional[float] = None
    state_of_health: float = Field(default=100.0, ge=0.0, le=100.0)  # Battery health %
    cycles: Optional[int] = None  # Charge cycles
    backup_reserve_percent: float = Field(ge=0.0, le=100.0)
    operation_mode: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "PW-001-ABC123",
                "timestamp": "2024-01-20T14:30:00Z",
                "battery_charge_percent": 85.5,
                "battery_power_kw": -2.3,
                "solar_power_kw": 5.2,
                "grid_power_kw": -0.5,
                "home_power_kw": 2.4,
                "battery_temperature_c": 25.3,
                "inverter_temperature_c": 32.1,
                "voltage": 240.5,
                "frequency_hz": 60.0,
                "state_of_health": 98.5,
                "cycles": 1250,
                "backup_reserve_percent": 20.0,
                "operation_mode": "self_powered"
            }
        }


class TelemetryHistory(BaseModel):
    device_id: str
    start_time: datetime
    end_time: datetime
    data_points: List[Telemetry]
    summary: Optional[dict] = None


class Alert(BaseModel):
    alert_id: str
    device_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    metadata: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "ALERT-001",
                "device_id": "PW-001-ABC123",
                "alert_type": "low_battery",
                "severity": "warning",
                "message": "Battery charge below 20%",
                "timestamp": "2024-01-20T14:30:00Z",
                "acknowledged": False,
                "resolved": False
            }
        }


class HealthAnalysisRequest(BaseModel):
    device_id: str
    analysis_type: str = "comprehensive"  # comprehensive, battery, solar, grid
    include_recommendations: bool = True


class HealthAnalysisResponse(BaseModel):
    device_id: str
    overall_health_score: float = Field(ge=0.0, le=100.0)
    analysis: str
    recommendations: List[str]
    key_metrics: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)

