from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    POWERWALL = "powerwall"
    SOLAR_INVERTER = "solar_inverter"
    WALL_CONNECTOR = "wall_connector"


class OperationMode(str, Enum):
    BACKUP = "backup"
    SELF_POWERED = "self_powered"
    TIME_BASED_CONTROL = "time_based_control"
    ADVANCED = "advanced"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    STANDBY = "standby"
    CHARGING = "charging"
    DISCHARGING = "discharging"
    FAULT = "fault"
    UPDATING = "updating"


class ControlCommandType(str, Enum):
    CHARGE_NOW = "charge_now"
    STOP_CHARGING = "stop_charging"
    ISOLATE_FROM_GRID = "isolate_from_grid"
    REJOIN_GRID = "rejoin_grid"
    REBOOT = "reboot"
    FIRMWARE_UPDATE = "firmware_update"
    SET_BACKUP_RESERVE = "set_backup_reserve"
    SET_OPERATION_MODE = "set_operation_mode"


class DeviceConfig(BaseModel):
    backup_reserve_percent: float = Field(default=20.0, ge=0.0, le=100.0)
    operation_mode: OperationMode = OperationMode.SELF_POWERED
    grid_charging_enabled: bool = False
    storm_watch_enabled: bool = True
    time_of_use_enabled: bool = False
    firmware_version: str = "23.44.1"
    installation_date: Optional[datetime] = None


class ControlCommand(BaseModel):
    command: ControlCommandType
    parameters: Optional[dict] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class Device(BaseModel):
    device_id: str
    serial_number: str
    device_type: DeviceType
    model: str
    firmware_version: str
    status: DeviceStatus
    config: DeviceConfig
    location: Optional[str] = None
    installed_at: datetime
    last_seen: datetime
    battery_capacity_kwh: float = 13.5  # Powerwall 2 capacity
    solar_capacity_kw: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "PW-001-ABC123",
                "serial_number": "SN123456789",
                "device_type": "powerwall",
                "model": "Powerwall 2",
                "firmware_version": "23.44.1",
                "status": "online",
                "config": {
                    "backup_reserve_percent": 20.0,
                    "operation_mode": "self_powered",
                    "grid_charging_enabled": False,
                    "storm_watch_enabled": True
                },
                "location": "Garage",
                "installed_at": "2023-01-15T10:00:00Z",
                "last_seen": "2024-01-20T14:30:00Z",
                "battery_capacity_kwh": 13.5,
                "solar_capacity_kw": 8.5
            }
        }


class DeviceListResponse(BaseModel):
    devices: List[Device]
    total: int
    page: int = 1
    page_size: int = 50

