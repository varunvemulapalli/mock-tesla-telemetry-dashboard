from fastapi import APIRouter, HTTPException
from app.models.telemetry import HealthAnalysisRequest, HealthAnalysisResponse
from app.services.device_manager import device_manager
from app.services.gpt_service import get_gpt_service
from app.services.data_simulator import simulator

router = APIRouter(prefix="/api/health", tags=["health"])


@router.post("/analyze", response_model=HealthAnalysisResponse)
async def analyze_device_health(request: HealthAnalysisRequest):
    device = device_manager.get_device(request.device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {request.device_id} not found")
    
    gpt_service = get_gpt_service()
    if not gpt_service:
        return HealthAnalysisResponse(
            device_id=request.device_id,
            overall_health_score=85.0,
            analysis="AI health analysis is currently unavailable. Please check system status manually.",
            recommendations=[
                "Monitor battery charge levels",
                "Check for firmware updates",
                "Review system alerts",
            ],
            key_metrics={},
        )
    
    try:
        analysis = await gpt_service.analyze_device_health(
            device_id=request.device_id,
            analysis_type=request.analysis_type,
            include_recommendations=request.include_recommendations,
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health analysis failed: {str(e)}")


@router.get("/{device_id}/summary")
async def get_health_summary(device_id: str):
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    state = device_manager.get_device_state(device_id)
    simulator_state = simulator._device_states.get(device_id, {})
    
    return {
        "device_id": device_id,
        "status": device.status.value,
        "battery_charge_percent": simulator_state.get("battery_charge", 0),
        "battery_cycles": simulator_state.get("cycles", 0),
        "firmware_version": device.firmware_version,
        "last_seen": device.last_seen.isoformat(),
        "is_online": device.status.value in ["online", "charging", "discharging"],
        "alerts": [],
    }

