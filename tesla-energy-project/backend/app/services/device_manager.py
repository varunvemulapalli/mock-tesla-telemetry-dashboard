import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from app.models.device import (
    Device,
    DeviceType,
    DeviceStatus,
    DeviceConfig,
    ControlCommand,
    ControlCommandType,
    OperationMode,
)


class DeviceManager:
    def __init__(self):
        self._devices: Dict[str, Device] = {}
        self._command_queue: Dict[str, List[ControlCommand]] = {}
        self._device_states: Dict[str, dict] = {}
        self._initialize_default_devices()
    
    def _initialize_default_devices(self):
        default_devices = [
            {
                "device_id": "PW-001-ABC123",
                "serial_number": "SN123456789",
                "device_type": DeviceType.POWERWALL,
                "model": "Powerwall 1",
                "location": "Garage",
                "battery_capacity_kwh": 13.5,
                "solar_capacity_kw": 8.5,
            },
            {
                "device_id": "PW-002-XYZ789",
                "serial_number": "SN987654321",
                "device_type": DeviceType.POWERWALL,
                "model": "Powerwall 2",
                "location": "Basement",
                "battery_capacity_kwh": 13.5,
                "solar_capacity_kw": 12.0,
            },
            {
                "device_id": "SI-001-SOLAR1",
                "serial_number": "SN-SOLAR-001",
                "device_type": DeviceType.SOLAR_INVERTER,
                "model": "Solar Inverter 7.6kW",
                "location": "Roof",
                "solar_capacity_kw": 7.6,
            },
        ]
        
        for device_data in default_devices:
            device = Device(
                device_id=device_data["device_id"],
                serial_number=device_data["serial_number"],
                device_type=device_data["device_type"],
                model=device_data["model"],
                firmware_version="23.44.1",
                status=DeviceStatus.ONLINE,
                config=DeviceConfig(
                    backup_reserve_percent=20.0,
                    operation_mode=OperationMode.SELF_POWERED,
                    grid_charging_enabled=False,
                    storm_watch_enabled=True,
                    installation_date=datetime.utcnow() - timedelta(days=365),
                ),
                location=device_data.get("location"),
                installed_at=datetime.utcnow() - timedelta(days=365),
                last_seen=datetime.utcnow(),
                battery_capacity_kwh=device_data.get("battery_capacity_kwh", 13.5),
                solar_capacity_kw=device_data.get("solar_capacity_kw"),
            )
            self._devices[device.device_id] = device
            self._command_queue[device.device_id] = []
            self._device_states[device.device_id] = {
                "is_isolated": False,
                "is_charging": False,
                "is_discharging": False,
                "last_command": None,
            }
    
    def get_device(self, device_id: str) -> Optional[Device]:
        return self._devices.get(device_id)
    
    def get_all_devices(self) -> List[Device]:
        return list(self._devices.values())
    
    def register_device(self, device: Device) -> Device:
        self._devices[device.device_id] = device
        self._command_queue[device.device_id] = []
        self._device_states[device.device_id] = {
            "is_isolated": False,
            "is_charging": False,
            "is_discharging": False,
            "last_command": None,
        }
        return device
    
    def update_device_config(self, device_id: str, config: DeviceConfig) -> Optional[Device]:
        device = self._devices.get(device_id)
        if device:
            device.config = config
            device.last_seen = datetime.utcnow()
        return device
    
    def update_device_status(self, device_id: str, status: DeviceStatus) -> Optional[Device]:
        device = self._devices.get(device_id)
        if device:
            device.status = status
            device.last_seen = datetime.utcnow()
        return device
    
    async def execute_command(self, device_id: str, command: ControlCommand) -> dict:
        device = self.get_device(device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        if device_id not in self._command_queue:
            self._command_queue[device_id] = []
        self._command_queue[device_id].append(command)
        
        state = self._device_states[device_id]
        result = {
            "command_id": f"CMD-{datetime.utcnow().timestamp()}",
            "device_id": device_id,
            "command": command.command,
            "status": "executing",
            "timestamp": datetime.utcnow(),
        }
        
        await asyncio.sleep(0.5)
        
        if command.command == ControlCommandType.CHARGE_NOW:
            state["is_charging"] = True
            state["is_discharging"] = False
            state["charge_until"] = datetime.utcnow().timestamp() + 1800
            device.status = DeviceStatus.CHARGING
            result["status"] = "completed"
            result["message"] = "Battery charging initiated - will charge for 30 minutes or until full"
        
        elif command.command == ControlCommandType.STOP_CHARGING:
            state["is_charging"] = False
            state["charge_until"] = 0
            state["is_discharging"] = False
            if device.status == DeviceStatus.CHARGING:
                device.status = DeviceStatus.ONLINE
            result["status"] = "completed"
            result["message"] = "Charging stopped - device returning to normal operation"
        
        elif command.command == ControlCommandType.ISOLATE_FROM_GRID:
            state["is_isolated"] = True
            result["status"] = "completed"
            result["message"] = "Device isolated from grid"
        
        elif command.command == ControlCommandType.REJOIN_GRID:
            state["is_isolated"] = False
            result["status"] = "completed"
            result["message"] = "Device reconnected to grid"
        
        elif command.command == ControlCommandType.REBOOT:
            device.status = DeviceStatus.STANDBY
            result["status"] = "completed"
            result["message"] = "Device rebooting - will be back online in a few seconds"
            asyncio.create_task(self._simulate_reboot_recovery(device_id))
        
        elif command.command == ControlCommandType.FIRMWARE_UPDATE:
            device.status = DeviceStatus.UPDATING
            result["status"] = "in_progress"
            result["message"] = "Firmware update in progress..."
            await asyncio.sleep(3)
            if command.parameters and "version" in command.parameters:
                device.firmware_version = command.parameters["version"]
            device.status = DeviceStatus.ONLINE
            result["status"] = "completed"
            result["message"] = "Firmware update completed"
        
        elif command.command == ControlCommandType.SET_BACKUP_RESERVE:
            if command.parameters and "percent" in command.parameters:
                device.config.backup_reserve_percent = command.parameters["percent"]
            result["status"] = "completed"
            result["message"] = f"Backup reserve set to {device.config.backup_reserve_percent}%"
        
        elif command.command == ControlCommandType.SET_OPERATION_MODE:
            if command.parameters and "mode" in command.parameters:
                device.config.operation_mode = OperationMode(command.parameters["mode"])
            result["status"] = "completed"
            result["message"] = f"Operation mode set to {device.config.operation_mode}"
        
        state["last_command"] = result
        device.last_seen = datetime.utcnow()
        
        return result
    
    async def _simulate_reboot_recovery(self, device_id: str):
        await asyncio.sleep(3)
        device = self.get_device(device_id)
        if device and device.status == DeviceStatus.STANDBY:
            device.status = DeviceStatus.ONLINE
    
    def get_device_state(self, device_id: str) -> Optional[dict]:
        return self._device_states.get(device_id)
    
    def get_command_history(self, device_id: str) -> List[ControlCommand]:
        return self._command_queue.get(device_id, [])


device_manager = DeviceManager()

