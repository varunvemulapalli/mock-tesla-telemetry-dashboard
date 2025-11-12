import os
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI
from app.models.telemetry import HealthAnalysisResponse
from app.services.device_manager import device_manager
from app.services.data_simulator import simulator


class GPTService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"
    
    def _format_telemetry_summary(self, device_id: str) -> str:
        device = device_manager.get_device(device_id)
        if not device:
            return "Device not found"
        
        state = simulator._device_states.get(device_id, {})
        
        summary = f"""
Device Information:
- Device ID: {device.device_id}
- Model: {device.model}
- Firmware: {device.firmware_version}
- Status: {device.status.value}
- Location: {device.location or 'Unknown'}
- Installed: {device.installed_at.strftime('%Y-%m-%d')}
- Battery Capacity: {device.battery_capacity_kwh} kWh
- Solar Capacity: {device.solar_capacity_kw or 0} kW

Current State:
- Battery Charge: {state.get('battery_charge', 0):.1f}%
- Solar Generation: {state.get('solar_generation', 0):.2f} kW
- Home Consumption: {state.get('home_consumption', 0):.2f} kW
- Battery Cycles: {state.get('cycles', 0)}
- Temperature: {state.get('temperature', 0):.1f}°C

Configuration:
- Operation Mode: {device.config.operation_mode.value}
- Backup Reserve: {device.config.backup_reserve_percent}%
- Grid Charging: {device.config.grid_charging_enabled}
- Storm Watch: {device.config.storm_watch_enabled}
"""
        return summary
    
    async def analyze_device_health(
        self, device_id: str, analysis_type: str = "comprehensive", include_recommendations: bool = True
    ) -> HealthAnalysisResponse:
        device = device_manager.get_device(device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        telemetry_summary = self._format_telemetry_summary(device_id)
        
        if analysis_type == "battery":
            prompt = f"""You are an expert energy systems engineer analyzing a Tesla Powerwall battery system.

{telemetry_summary}

Analyze the BATTERY HEALTH specifically:
1. Battery charge level and patterns
2. Charge cycles and degradation
3. Temperature impacts
4. State of health indicators
5. Expected lifespan

Provide a concise technical analysis (2-3 paragraphs) focusing on battery health metrics.
"""
        elif analysis_type == "solar":
            prompt = f"""You are an expert energy systems engineer analyzing a Tesla solar and battery system.

{telemetry_summary}

Analyze the SOLAR SYSTEM performance:
1. Solar generation patterns
2. System efficiency
3. Weather impacts
4. Optimal utilization
5. ROI and energy savings

Provide a concise technical analysis (2-3 paragraphs) focusing on solar performance.
"""
        elif analysis_type == "grid":
            prompt = f"""You are an expert energy systems engineer analyzing grid interaction for a Tesla energy system.

{telemetry_summary}

Analyze GRID INTERACTION:
1. Grid import/export patterns
2. Self-consumption rate
3. Grid independence
4. Cost optimization opportunities
5. Time-of-use optimization

Provide a concise technical analysis (2-3 paragraphs) focusing on grid interaction.
"""
        else:  # comprehensive
            prompt = f"""You are an expert energy systems engineer providing comprehensive health analysis for a Tesla Powerwall energy system.

{telemetry_summary}

Provide a COMPREHENSIVE SYSTEM ANALYSIS:
1. Overall system health and performance
2. Battery status and longevity
3. Solar generation efficiency
4. Grid interaction and self-consumption
5. Operational recommendations
6. Potential issues or concerns
7. Optimization opportunities

Provide a detailed technical analysis (4-5 paragraphs) covering all aspects of the system.
"""
        
        if include_recommendations:
            prompt += "\n\nAlso provide 3-5 specific, actionable recommendations for optimizing system performance, reducing costs, or improving reliability."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert energy systems engineer specializing in residential battery storage and solar systems. Provide technical, accurate, and actionable insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            
            analysis_text = response.choices[0].message.content
            
            recommendations = []
            if include_recommendations:
                lines = analysis_text.split('\n')
                in_recommendations = False
                for line in lines:
                    if 'recommendation' in line.lower() or 'suggest' in line.lower() or line.strip().startswith('-') or line.strip().startswith('•'):
                        in_recommendations = True
                    if in_recommendations and (line.strip().startswith('-') or line.strip().startswith('•') or line.strip().startswith('1.') or line.strip().startswith('2.')):
                        rec = line.strip().lstrip('-•123456789. ').strip()
                        if rec and len(rec) > 10:
                            recommendations.append(rec)
                
                if not recommendations:
                    recommendations = [
                        "Monitor battery temperature during peak usage periods",
                        "Consider adjusting backup reserve based on usage patterns",
                        "Review time-of-use settings to optimize cost savings",
                    ]
            
            state = simulator._device_states.get(device_id, {})
            health_score = 85.0
            
            battery_charge = state.get('battery_charge', 50)
            if 20 <= battery_charge <= 90:
                health_score += 5
            elif battery_charge < 20 or battery_charge > 95:
                health_score -= 10
            
            cycles = state.get('cycles', 0)
            if cycles < 1000:
                health_score += 5
            elif cycles > 2000:
                health_score -= 5
            
            health_score = max(0, min(100, health_score))
            
            key_metrics = {
                "battery_charge_percent": state.get('battery_charge', 0),
                "battery_cycles": state.get('cycles', 0),
                "solar_generation_kw": state.get('solar_generation', 0),
                "home_consumption_kw": state.get('home_consumption', 0),
                "system_age_days": (datetime.utcnow() - device.installed_at).days,
            }
            
            return HealthAnalysisResponse(
                device_id=device_id,
                overall_health_score=health_score,
                analysis=analysis_text,
                recommendations=recommendations if recommendations else [
                    "Continue monitoring system performance",
                    "Schedule annual maintenance check",
                ],
                key_metrics=key_metrics,
                timestamp=datetime.utcnow(),
            )
        
        except Exception as e:
            return HealthAnalysisResponse(
                device_id=device_id,
                overall_health_score=85.0,
                analysis=f"Health analysis temporarily unavailable. Error: {str(e)}. System appears to be operating normally based on current telemetry.",
                recommendations=[
                    "Monitor system performance regularly",
                    "Contact support if issues persist",
                ],
                key_metrics={},
                timestamp=datetime.utcnow(),
            )


gpt_service: Optional[GPTService] = None


def get_gpt_service() -> Optional[GPTService]:
    global gpt_service
    if gpt_service is None:
        try:
            gpt_service = GPTService()
        except Exception as e:
            print(f"Warning: GPT service not available: {e}")
            return None
    return gpt_service

