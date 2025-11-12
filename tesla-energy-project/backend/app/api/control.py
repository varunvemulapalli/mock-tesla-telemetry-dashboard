from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.device import ControlCommand
from app.services.device_manager import device_manager
from app.services.websocket_manager import websocket_manager

router = APIRouter(prefix="/api/control", tags=["control"])


def serialize_datetime_in_dict(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_datetime_in_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime_in_dict(item) for item in obj]
    else:
        return obj


@router.post("/{device_id}")
async def execute_control_command(device_id: str, command: ControlCommand):
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    result = await device_manager.execute_command(device_id, command)
    serialized_result = serialize_datetime_in_dict(result)
    
    await websocket_manager.broadcast_to_device(device_id, {
        "type": "command_result",
        "data": serialized_result,
    })
    
    return serialized_result


@router.get("/{device_id}/history")
async def get_command_history(device_id: str, limit: int = 50):
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    history = device_manager.get_command_history(device_id)
    return {
        "device_id": device_id,
        "commands": [cmd.model_dump() for cmd in history[-limit:]],
        "total": len(history),
    }

