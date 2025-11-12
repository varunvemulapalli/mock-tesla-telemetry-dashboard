from typing import Dict, Set, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import json
from app.models.telemetry import Telemetry
from app.services.data_simulator import simulator


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        if device_id not in self.active_connections:
            self.active_connections[device_id] = set()
        self.active_connections[device_id].add(websocket)
        print(f"WebSocket connected for device {device_id}. Total connections: {len(self.active_connections[device_id])}")
    
    def disconnect(self, websocket: WebSocket, device_id: str):
        if device_id in self.active_connections:
            self.active_connections[device_id].discard(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]
        print(f"WebSocket disconnected for device {device_id}")
    
    async def send_telemetry(self, device_id: str, telemetry: Telemetry):
        if device_id not in self.active_connections:
            return
        
        telemetry_dict = telemetry.model_dump()
        telemetry_dict["timestamp"] = telemetry_dict["timestamp"].isoformat()
        message = json.dumps(telemetry_dict)
        
        disconnected = set()
        for connection in self.active_connections[device_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)
        
        for connection in disconnected:
            self.disconnect(connection, device_id)
    
    def _serialize_datetime(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        else:
            return obj
    
    async def broadcast_to_device(self, device_id: str, message: dict):
        if device_id not in self.active_connections:
            return
        
        serialized_message = self._serialize_datetime(message)
        message_json = json.dumps(serialized_message)
        disconnected = set()
        for connection in self.active_connections[device_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                print(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(connection)
        
        for connection in disconnected:
            self.disconnect(connection, device_id)
    
    def get_connection_count(self, device_id: str) -> int:
        return len(self.active_connections.get(device_id, set()))


websocket_manager = WebSocketManager()

