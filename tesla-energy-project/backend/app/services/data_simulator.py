import asyncio
import random
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import httpx
from app.models.telemetry import Telemetry
from app.models.device import DeviceStatus
from app.services.device_manager import device_manager


class DataSimulator:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.running = False
        self._device_states: Dict[str, dict] = {}
        self._initialize_device_states()
    
    def _initialize_device_states(self):
        devices = device_manager.get_all_devices()
        for device in devices:
            self._device_states[device.device_id] = {
                "battery_charge": random.uniform(20, 95),
                "solar_generation": 0.0,
                "home_consumption": random.uniform(1.0, 3.0),
                "grid_power": 0.0,
                "battery_power": 0.0,
                "temperature": random.uniform(20, 30),
                "day_cycle": 0,
                "weather_factor": random.uniform(0.7, 1.0),
                "cycles": random.randint(500, 2000),
            }
    
    def _simulate_solar_generation(self, device_id: str, hour: float) -> float:
        state = self._device_states[device_id]
        device = device_manager.get_device(device_id)
        
        if not device or not device.solar_capacity_kw:
            return 0.0
        
        peak_hour = 12.0
        
        if 6 <= hour <= 20:
            distance_from_peak = abs(hour - peak_hour)
            intensity = max(0, 1 - (distance_from_peak / 6) ** 2)
            intensity *= random.uniform(0.8, 1.0)
            intensity *= state["weather_factor"]
            return device.solar_capacity_kw * intensity
        return 0.0
    
    def _simulate_home_consumption(self, device_id: str, hour: float) -> float:
        state = self._device_states[device_id]
        base_consumption = state["home_consumption"]
        
        if 7 <= hour <= 9:
            multiplier = random.uniform(1.3, 1.8)
        elif 17 <= hour <= 21:
            multiplier = random.uniform(1.5, 2.2)
        elif 22 <= hour or hour <= 6:
            multiplier = random.uniform(0.5, 0.8)
        else:
            multiplier = random.uniform(0.8, 1.2)
        
        return base_consumption * multiplier
    
    def _simulate_battery_behavior(
        self, device_id: str, solar: float, home: float, hour: float
    ) -> tuple[float, float]:
        state = self._device_states[device_id]
        device = device_manager.get_device(device_id)
        device_state = device_manager.get_device_state(device_id)
        
        if not device:
            return 0.0, state["battery_charge"]
        
        current_charge = state["battery_charge"]
        battery_capacity_kwh = device.battery_capacity_kwh
        backup_reserve = device.config.backup_reserve_percent
        
        net_power = solar - home
        max_charge_rate = 5.0
        max_discharge_rate = 5.0
        
        is_isolated = device_state.get("is_isolated", False) if device_state else False
        charge_until = device_state.get("charge_until", 0) if device_state else 0
        is_charging_forced = charge_until > datetime.utcnow().timestamp() if charge_until else False
        is_discharging_forced = device_state.get("is_discharging", False) if device_state else False
        
        if charge_until > 0 and charge_until <= datetime.utcnow().timestamp():
            if device_state:
                device_state["charge_until"] = 0
                device_state["is_charging"] = False
                is_charging_forced = False
        
        battery_power = 0.0
        
        if is_charging_forced:
            if current_charge < 100:
                remaining_solar = max(0, solar - home)
                
                if remaining_solar > 0:
                    battery_power = min(remaining_solar, max_charge_rate)
                    if device.config.grid_charging_enabled and battery_power < max_charge_rate:
                        battery_power = min(max_charge_rate, battery_power + 2.0)
                elif device.config.grid_charging_enabled:
                    battery_power = min(max_charge_rate, 4.0)
                elif solar > 0:
                    battery_power = min(solar, max_charge_rate, 2.0)
                else:
                    battery_power = min(max_charge_rate, 1.5)
            else:
                battery_power = 0.0
        
        elif is_discharging_forced and current_charge > backup_reserve:
            available_charge = (current_charge - backup_reserve) / 100.0 * battery_capacity_kwh
            battery_power = -min(max_discharge_rate, available_charge * 2, abs(home))
        
        elif is_isolated:
            if home > 0 and current_charge > backup_reserve:
                available_charge = (current_charge - backup_reserve) / 100.0 * battery_capacity_kwh
                battery_power = -min(max_discharge_rate, home, available_charge * 2)
            if solar > home and current_charge < 100:
                excess_solar = solar - home
                battery_power += min(excess_solar, max_charge_rate)
        
        elif device.config.operation_mode.value == "self_powered":
            if net_power > 0 and current_charge < 100:
                battery_power = min(net_power, max_charge_rate)
            elif net_power < 0 and current_charge > backup_reserve:
                available_charge = (current_charge - backup_reserve) / 100.0 * battery_capacity_kwh
                if available_charge > 0:
                    battery_power = max(net_power, -min(abs(net_power), max_discharge_rate, available_charge * 2))
        
        elif device.config.operation_mode.value == "backup":
            if net_power > 0 and current_charge < 100:
                battery_power = min(net_power, max_charge_rate)
        
        elif device.config.operation_mode.value == "time_based_control":
            if 10 <= hour <= 14 and current_charge > backup_reserve + 10:
                battery_power = -min(max_discharge_rate, 2.0)
            elif (22 <= hour or hour <= 6) and net_power > 0 and current_charge < 100:
                battery_power = min(net_power, max_charge_rate)
        
        time_interval_minutes = 5.0 / 60.0
        energy_change_kwh = battery_power * time_interval_minutes
        charge_change_percent = (energy_change_kwh / battery_capacity_kwh) * 100
        
        if battery_power > 0:
            new_charge = min(100.0, current_charge + charge_change_percent)
        else:
            new_charge = max(backup_reserve, current_charge + charge_change_percent)
        
        state["battery_charge"] = new_charge
        
        charge_until = device_state.get("charge_until", 0) if device_state else 0
        is_charging_forced = charge_until > datetime.utcnow().timestamp() if charge_until else False
        
        if device_state:
            if is_charging_forced:
                device_state["is_charging"] = True
                device_state["is_discharging"] = False
                if device.status.value != "charging":
                    device.status = DeviceStatus.CHARGING
            elif battery_power > 0.5:
                device_state["is_charging"] = True
                device_state["is_discharging"] = False
                if device.status.value != "charging":
                    device.status = DeviceStatus.CHARGING
            elif battery_power < -0.5:
                device_state["is_charging"] = False
                device_state["is_discharging"] = True
                if device.status.value != "discharging":
                    device.status = DeviceStatus.DISCHARGING
            else:
                if not is_charging_forced:
                    if device.status.value in ["charging", "discharging"]:
                        device_state["is_charging"] = False
                        device_state["is_discharging"] = False
                        device.status = DeviceStatus.ONLINE
        
        return battery_power, new_charge
    
    def _calculate_grid_power(self, device_id: str, solar: float, home: float, battery: float) -> float:
        device_state = device_manager.get_device_state(device_id)
        is_isolated = device_state.get("is_isolated", False) if device_state else False
        
        if is_isolated:
            return 0.0
        
        return home - solar - battery
    
    def generate_telemetry(self, device_id: str, historical: bool = False, historical_charge: Optional[float] = None, historical_timestamp: Optional[datetime] = None) -> Telemetry:
        device = device_manager.get_device(device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        state = self._device_states[device_id]
        
        if historical:
            if historical_timestamp:
                hour = historical_timestamp.hour + historical_timestamp.minute / 60.0
            else:
                hour = random.uniform(6, 20)
            weather_factor = random.uniform(0.7, 1.0)
            if historical_charge is not None:
                current_charge = historical_charge
            else:
                current_charge = state["battery_charge"]
        else:
            state["day_cycle"] = (state["day_cycle"] + 0.0167) % 24
            hour = state["day_cycle"]
            state["weather_factor"] += random.uniform(-0.02, 0.02)
            state["weather_factor"] = max(0.3, min(1.0, state["weather_factor"]))
            weather_factor = state["weather_factor"]
            current_charge = state["battery_charge"]
        
        if historical:
            solar_power = self._simulate_solar_generation_historical(device_id, hour, weather_factor)
            home_power = self._simulate_home_consumption_historical(device_id, hour)
            battery_power, battery_charge = self._simulate_battery_behavior_historical(
                device_id, solar_power, home_power, hour, current_charge, reverse=True
            )
        else:
            solar_power = self._simulate_solar_generation(device_id, hour)
            home_power = self._simulate_home_consumption(device_id, hour)
            battery_power, battery_charge = self._simulate_battery_behavior(
                device_id, solar_power, home_power, hour
            )
        
        grid_power = self._calculate_grid_power(device_id, solar_power, home_power, battery_power)
        
        base_temp = 22.0
        temp_variation = abs(battery_power) * 0.5
        time_variation = math.sin((hour - 6) * math.pi / 12) * 3
        temperature = base_temp + temp_variation + time_variation + random.uniform(-1, 1)
        
        cycles = state["cycles"]
        soh = max(80.0, 100.0 - (cycles / 10000) * 10)
        
        battery_charge = max(0.0, min(100.0, battery_charge))
        battery_power = float(battery_power) if battery_power is not None else 0.0
        solar_power = max(0.0, float(solar_power) if solar_power is not None else 0.0)
        grid_power = float(grid_power) if grid_power is not None else 0.0
        home_power = max(0.0, float(home_power) if home_power is not None else 0.0)
        temperature = float(temperature) if temperature is not None else 25.0
        soh = max(0.0, min(100.0, float(soh) if soh is not None else 100.0))
        cycles = int(cycles) if cycles is not None else 0
        
        if historical and historical_timestamp:
            timestamp = historical_timestamp
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = datetime.utcnow()
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        telemetry = Telemetry(
            device_id=device_id,
            timestamp=timestamp,
            battery_charge_percent=battery_charge,
            battery_power_kw=battery_power,
            solar_power_kw=solar_power,
            grid_power_kw=grid_power,
            home_power_kw=home_power,
            battery_temperature_c=temperature,
            inverter_temperature_c=temperature + random.uniform(5, 10),
            voltage=240.0 + random.uniform(-2, 2),
            frequency_hz=60.0 + random.uniform(-0.1, 0.1),
            state_of_health=soh,
            cycles=cycles,
            backup_reserve_percent=device.config.backup_reserve_percent,
            operation_mode=device.config.operation_mode.value,
        )
        
        return telemetry
    
    def _simulate_solar_generation_historical(self, device_id: str, hour: float, weather_factor: float) -> float:
        device = device_manager.get_device(device_id)
        
        if not device or not device.solar_capacity_kw:
            return 0.0
        
        peak_hour = 12.0
        
        if 6 <= hour <= 20:
            distance_from_peak = abs(hour - peak_hour)
            intensity = max(0, 1 - (distance_from_peak / 6) ** 2)
            intensity *= random.uniform(0.8, 1.0)
            intensity *= weather_factor
            return device.solar_capacity_kw * intensity
        return 0.0
    
    def _simulate_home_consumption_historical(self, device_id: str, hour: float) -> float:
        state = self._device_states[device_id]
        base_consumption = state["home_consumption"]
        
        if 7 <= hour <= 9:
            multiplier = random.uniform(1.3, 1.8)
        elif 17 <= hour <= 21:
            multiplier = random.uniform(1.5, 2.2)
        elif 22 <= hour or hour <= 6:
            multiplier = random.uniform(0.5, 0.8)
        else:
            multiplier = random.uniform(0.8, 1.2)
        
        return base_consumption * multiplier
    
    def _simulate_battery_behavior_historical(
        self, device_id: str, solar: float, home: float, hour: float, current_charge: float, reverse: bool = True
    ) -> tuple[float, float]:
        device = device_manager.get_device(device_id)
        device_state = device_manager.get_device_state(device_id)
        
        if not device:
            return 0.0, current_charge
        
        battery_capacity_kwh = device.battery_capacity_kwh
        backup_reserve = device.config.backup_reserve_percent
        
        net_power = solar - home
        max_charge_rate = 5.0
        max_discharge_rate = 5.0
        
        is_charging_forced = False
        if device_state:
            charge_until = device_state.get("charge_until", 0)
            is_charging_forced = charge_until > datetime.utcnow().timestamp() if charge_until else False
        
        battery_power = 0.0
        
        if is_charging_forced and current_charge < 100:
            remaining_solar = max(0, solar - home)
            if remaining_solar > 0:
                battery_power = min(remaining_solar, max_charge_rate)
            elif device.config.grid_charging_enabled:
                battery_power = min(max_charge_rate, 4.0)
            elif solar > 0:
                battery_power = min(solar, max_charge_rate, 2.0)
            else:
                battery_power = min(max_charge_rate, 1.5)
        elif device.config.operation_mode.value == "self_powered":
            if net_power > 0 and current_charge < 100:
                battery_power = min(net_power, max_charge_rate)
            elif net_power < 0 and current_charge > backup_reserve:
                available_charge = (current_charge - backup_reserve) / 100.0 * battery_capacity_kwh
                if available_charge > 0:
                    battery_power = max(net_power, -min(abs(net_power), max_discharge_rate, available_charge * 2))
        elif device.config.operation_mode.value == "backup":
            if net_power > 0 and current_charge < 100:
                battery_power = min(net_power, max_charge_rate)
        elif device.config.operation_mode.value == "time_based_control":
            if 10 <= hour <= 14 and current_charge > backup_reserve + 10:
                battery_power = -min(max_discharge_rate, 2.0)
            elif (22 <= hour or hour <= 6) and net_power > 0 and current_charge < 100:
                battery_power = min(net_power, max_charge_rate)
        
        time_interval_minutes = 5.0 / 60.0
        energy_change_kwh = battery_power * time_interval_minutes
        charge_change_percent = (energy_change_kwh / battery_capacity_kwh) * 100
        
        if reverse:
            if battery_power > 0:
                old_charge = max(backup_reserve, current_charge - charge_change_percent)
            else:
                old_charge = min(100.0, current_charge - charge_change_percent)
            return battery_power, old_charge
        else:
            if battery_power > 0:
                new_charge = min(100.0, current_charge + charge_change_percent)
            else:
                new_charge = max(backup_reserve, current_charge + charge_change_percent)
            return battery_power, new_charge
    
    async def send_telemetry(self, telemetry: Telemetry):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/telemetry",
                    json=telemetry.model_dump(),
                    timeout=5.0,
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Error sending telemetry: {e}")
                return False
    
    async def run(self, interval_seconds: float = 5.0):
        self.running = True
        print("Data Simulator started...")
        
        while self.running:
            try:
                devices = device_manager.get_all_devices()
                for device in devices:
                    if device.status.value in ["online", "charging", "discharging"]:
                        telemetry = self.generate_telemetry(device.device_id)
                        await asyncio.sleep(0.1)
                
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                print(f"Error in simulator loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    def stop(self):
        self.running = False


simulator = DataSimulator()


if __name__ == "__main__":
    import sys
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    sim = DataSimulator(api_url=api_url)
    
    try:
        asyncio.run(sim.run(interval_seconds=5.0))
    except KeyboardInterrupt:
        print("\nStopping simulator...")
        sim.stop()

