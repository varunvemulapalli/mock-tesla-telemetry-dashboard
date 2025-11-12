from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import asyncio
from app.models.telemetry import Telemetry, TelemetryHistory
from app.services.device_manager import device_manager
from app.services.data_simulator import simulator
from app.services.websocket_manager import websocket_manager
from app.utils.analytics import calculate_statistics, detect_anomalies, calculate_energy_savings

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])

_telemetry_store: dict[str, List[Telemetry]] = {}


@router.post("", response_model=Telemetry, status_code=201)
async def create_telemetry(telemetry: Telemetry):
    device = device_manager.get_device(telemetry.device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {telemetry.device_id} not found")
    
    if telemetry.device_id not in _telemetry_store:
        _telemetry_store[telemetry.device_id] = []
    _telemetry_store[telemetry.device_id].append(telemetry)
    
    if len(_telemetry_store[telemetry.device_id]) > 1000:
        _telemetry_store[telemetry.device_id] = _telemetry_store[telemetry.device_id][-1000:]
    
    await websocket_manager.send_telemetry(telemetry.device_id, telemetry)
    
    return telemetry


@router.get("/{device_id}", response_model=Telemetry)
async def get_latest_telemetry(device_id: str):
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    try:
        telemetry = simulator.generate_telemetry(device_id)
        
        if not telemetry.voltage:
            telemetry.voltage = 240.0
        if not telemetry.frequency_hz:
            telemetry.frequency_hz = 60.0
        if not telemetry.inverter_temperature_c:
            telemetry.inverter_temperature_c = telemetry.battery_temperature_c + 5.0
        
        if device_id not in _telemetry_store:
            _telemetry_store[device_id] = []
        _telemetry_store[device_id].append(telemetry)
        
        if len(_telemetry_store[device_id]) > 1000:
            def make_aware_sort(ts: datetime) -> datetime:
                if ts.tzinfo is None:
                    return ts.replace(tzinfo=timezone.utc)
                return ts
            _telemetry_store[device_id].sort(key=lambda x: make_aware_sort(x.timestamp), reverse=True)
            _telemetry_store[device_id] = _telemetry_store[device_id][:1000]
            _telemetry_store[device_id].sort(key=lambda x: make_aware_sort(x.timestamp))
        
        return telemetry
    except Exception as e:
        device_state = device_manager.get_device_state(device_id) or {}
        simulator_state = simulator._device_states.get(device_id, {})
        
        timestamp = datetime.utcnow()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        return Telemetry(
            device_id=device_id,
            timestamp=timestamp,
            battery_charge_percent=simulator_state.get("battery_charge", 50.0),
            battery_power_kw=0.0,
            solar_power_kw=0.0,
            grid_power_kw=0.0,
            home_power_kw=2.0,
            battery_temperature_c=25.0,
            inverter_temperature_c=30.0,
            voltage=240.0,
            frequency_hz=60.0,
            state_of_health=100.0,
            cycles=0,
            backup_reserve_percent=device.config.backup_reserve_percent,
            operation_mode=device.config.operation_mode.value,
        )


@router.get("/{device_id}/history", response_model=TelemetryHistory)
async def get_telemetry_history(
    device_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
):
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)
    
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    stored = _telemetry_store.get(device_id, [])
    
    def make_aware(ts: datetime) -> datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    
    filtered = []
    for t in stored:
        t_ts = make_aware(t.timestamp)
        if start_time <= t_ts <= end_time:
            if t.timestamp.tzinfo is None:
                t.timestamp = t_ts
            filtered.append(t)
    
    if len(filtered) < limit:
        generated = []
        time_range_minutes = int((end_time - start_time).total_seconds() / 60)
        needed = min(limit - len(filtered), time_range_minutes, 200)
        
        current_state = simulator._device_states.get(device_id, {})
        current_charge = current_state.get("battery_charge", 50.0)
        
        if len(filtered) > 0:
            latest_time = max(make_aware(t.timestamp) for t in filtered)
            latest_telemetry = next((t for t in filtered if make_aware(t.timestamp) == latest_time), None)
            if latest_telemetry:
                current_charge = latest_telemetry.battery_charge_percent or current_charge
            current_time = latest_time - timedelta(minutes=1)
            historical_charge = current_charge
        else:
            current_time = start_time
            historical_charge = current_charge
        
        for i in range(needed):
            if current_time < start_time:
                current_time = start_time
            if current_time > end_time:
                break
            
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)
            
            telemetry = simulator.generate_telemetry(
                device_id, 
                historical=True, 
                historical_charge=historical_charge,
                historical_timestamp=current_time
            )
            
            historical_charge = telemetry.battery_charge_percent
            
            generated.insert(0, telemetry)
            current_time = current_time - timedelta(minutes=1)
            
            if len(generated) >= needed:
                break
        
        filtered.extend(generated)
        
        if device_id not in _telemetry_store:
            _telemetry_store[device_id] = []
        _telemetry_store[device_id].extend(generated)
        if len(_telemetry_store[device_id]) > 1000:
            _telemetry_store[device_id].sort(key=lambda x: make_aware(x.timestamp), reverse=True)
            _telemetry_store[device_id] = _telemetry_store[device_id][:1000]
            _telemetry_store[device_id].sort(key=lambda x: make_aware(x.timestamp))
    
    filtered.sort(key=lambda x: make_aware(x.timestamp))
    filtered = filtered[-limit:]
    
    summary = calculate_statistics(filtered)
    
    return TelemetryHistory(
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        data_points=filtered,
        summary=summary,
    )


@router.get("/{device_id}/analytics")
async def get_telemetry_analytics(device_id: str, hours: int = 24):
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    from datetime import timezone
    end_time = datetime.utcnow()
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    
    def make_aware(ts: datetime) -> datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    
    stored = _telemetry_store.get(device_id, [])
    filtered = [t for t in stored if start_time <= make_aware(t.timestamp) <= end_time]
    
    if len(filtered) < 10:
        current_state = simulator._device_states.get(device_id, {})
        current_charge = current_state.get("battery_charge", 50.0)
        historical_charge = current_charge
        
        current_time = start_time
        while current_time <= end_time and len(filtered) < 100:
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)
            telemetry = simulator.generate_telemetry(
                device_id, 
                historical=True, 
                historical_charge=historical_charge,
                historical_timestamp=current_time
            )
            historical_charge = telemetry.battery_charge_percent
            filtered.append(telemetry)
            current_time += timedelta(minutes=15)
    
    stats = calculate_statistics(filtered)
    anomalies = detect_anomalies(filtered)
    savings = calculate_energy_savings(filtered)
    
    return {
        "device_id": device_id,
        "period": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "hours": hours,
        },
        "statistics": stats,
        "anomalies": anomalies,
        "energy_savings": savings,
    }


@router.websocket("/ws/{device_id}")
async def websocket_telemetry(websocket: WebSocket, device_id: str):
    device = device_manager.get_device(device_id)
    if not device:
        await websocket.close(code=1008, reason=f"Device {device_id} not found")
        return
    
    await websocket_manager.connect(websocket, device_id)
    
    try:
        initial_telemetry = simulator.generate_telemetry(device_id)
        await websocket_manager.send_telemetry(device_id, initial_telemetry)
        
        while True:
            await asyncio.sleep(5)
            telemetry = simulator.generate_telemetry(device_id)
            await websocket_manager.send_telemetry(device_id, telemetry)
            
            if device_id not in _telemetry_store:
                _telemetry_store[device_id] = []
            _telemetry_store[device_id].append(telemetry)
            if len(_telemetry_store[device_id]) > 1000:
                _telemetry_store[device_id] = _telemetry_store[device_id][-1000:]
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, device_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket, device_id)

