from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.device import Device, DeviceListResponse, DeviceConfig, ControlCommand
from app.services.device_manager import device_manager

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=DeviceListResponse)
async def list_devices(page: int = 1, page_size: int = 50):
    devices = device_manager.get_all_devices()
    total = len(devices)
    
    start = (page - 1) * page_size
    end = start + page_size
    paginated_devices = devices[start:end]
    
    return DeviceListResponse(
        devices=paginated_devices,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{device_id}", response_model=Device)
async def get_device(device_id: str):
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device


@router.post("", response_model=Device, status_code=201)
async def register_device(device: Device):
    existing = device_manager.get_device(device.device_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Device {device.device_id} already exists")
    
    return device_manager.register_device(device)


@router.put("/{device_id}/config", response_model=Device)
async def update_device_config(device_id: str, config: DeviceConfig):
    device = device_manager.update_device_config(device_id, config)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device


@router.get("/{device_id}/status")
async def get_device_status(device_id: str):
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    state = device_manager.get_device_state(device_id)
    command_history = device_manager.get_command_history(device_id)
    
    return {
        "device_id": device_id,
        "status": device.status.value,
        "state": state,
        "recent_commands": [cmd.model_dump() for cmd in command_history[-5:]],
    }

