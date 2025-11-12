from typing import List
import pandas as pd
import numpy as np
from app.models.telemetry import Telemetry


def calculate_statistics(telemetry_list: List[Telemetry]) -> dict:
    if not telemetry_list:
        return {}
    
    df = pd.DataFrame([t.model_dump() for t in telemetry_list])
    
    stats = {
        "battery_charge": {
            "mean": float(df["battery_charge_percent"].mean()),
            "min": float(df["battery_charge_percent"].min()),
            "max": float(df["battery_charge_percent"].max()),
            "std": float(df["battery_charge_percent"].std()),
        },
        "solar_generation": {
            "total_kwh": float(df["solar_power_kw"].sum() / 12),  # Assuming 5-minute intervals
            "mean_kw": float(df["solar_power_kw"].mean()),
            "peak_kw": float(df["solar_power_kw"].max()),
        },
        "home_consumption": {
            "total_kwh": float(df["home_power_kw"].sum() / 12),
            "mean_kw": float(df["home_power_kw"].mean()),
            "peak_kw": float(df["home_power_kw"].max()),
        },
        "grid_interaction": {
            "total_imported_kwh": float(df[df["grid_power_kw"] > 0]["grid_power_kw"].sum() / 12),
            "total_exported_kwh": float(abs(df[df["grid_power_kw"] < 0]["grid_power_kw"].sum() / 12)),
            "self_consumption_rate": float(
                (1 - abs(df[df["grid_power_kw"] < 0]["grid_power_kw"].sum()) / 
                 df["solar_power_kw"].sum()) * 100
                if df["solar_power_kw"].sum() > 0 else 0
            ),
        },
        "battery_cycles": {
            "estimated_daily_cycles": float(
                abs(df["battery_power_kw"].diff().fillna(0).sum()) / 13.5 / 2
            ),  # Rough estimate
        },
    }
    
    return stats


def detect_anomalies(telemetry_list: List[Telemetry]) -> List[dict]:
    if len(telemetry_list) < 10:
        return []
    
    df = pd.DataFrame([t.model_dump() for t in telemetry_list])
    anomalies = []
    
    charge_diff = df["battery_charge_percent"].diff()
    if (charge_diff < -10).any():
        idx = charge_diff.idxmin()
        anomalies.append({
            "type": "sudden_battery_drop",
            "timestamp": telemetry_list[idx].timestamp.isoformat(),
            "severity": "warning",
            "message": f"Battery charge dropped by {abs(charge_diff.iloc[idx]):.1f}%",
        })
    
    if (df["battery_temperature_c"] > 40).any():
        idx = df["battery_temperature_c"].idxmax()
        anomalies.append({
            "type": "high_temperature",
            "timestamp": telemetry_list[idx].timestamp.isoformat(),
            "severity": "critical",
            "message": f"Battery temperature reached {df['battery_temperature_c'].iloc[idx]:.1f}°C",
        })
    
    if (df["battery_charge_percent"] < 10).any():
        idx = df["battery_charge_percent"].idxmin()
        anomalies.append({
            "type": "low_battery",
            "timestamp": telemetry_list[idx].timestamp.isoformat(),
            "severity": "warning",
            "message": f"Battery charge dropped to {df['battery_charge_percent'].iloc[idx]:.1f}%",
        })
    
    return anomalies


def calculate_energy_savings(telemetry_list: List[Telemetry], grid_rate_per_kwh: float = 0.12) -> dict:
    if not telemetry_list:
        return {}
    
    df = pd.DataFrame([t.model_dump() for t in telemetry_list])
    
    interval_hours = 5 / 60
    
    solar_generated = df["solar_power_kw"].sum() * interval_hours
    grid_imported = df[df["grid_power_kw"] > 0]["grid_power_kw"].sum() * interval_hours
    grid_exported = abs(df[df["grid_power_kw"] < 0]["grid_power_kw"].sum() * interval_hours)
    
    home_consumption = df["home_power_kw"].sum() * interval_hours
    cost_without_solar = home_consumption * grid_rate_per_kwh
    
    net_imports = max(0, grid_imported - grid_exported * 0.5)
    cost_with_solar = net_imports * grid_rate_per_kwh
    
    savings = cost_without_solar - cost_with_solar
    
    return {
        "solar_generated_kwh": float(solar_generated),
        "grid_imported_kwh": float(grid_imported),
        "grid_exported_kwh": float(grid_exported),
        "home_consumption_kwh": float(home_consumption),
        "estimated_savings_usd": float(savings),
        "self_consumption_rate": float(
            (1 - grid_exported / solar_generated) * 100 if solar_generated > 0 else 0
        ),
    }

