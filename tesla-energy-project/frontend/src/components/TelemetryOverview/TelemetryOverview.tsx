import React from 'react';
import { Device, Telemetry } from '../../types/device';
import './TelemetryOverview.css';

interface TelemetryOverviewProps {
  device: Device;
  telemetry: Telemetry;
}

const TelemetryOverview: React.FC<TelemetryOverviewProps> = ({ device, telemetry }) => {
  // Safe number formatter with default values
  const formatPower = (power: number | undefined) => {
    if (power === undefined || power === null) return '0.00 kW';
    const absPower = Math.abs(power);
    return `${power >= 0 ? '+' : '-'}${absPower.toFixed(2)} kW`;
  };

  const formatNumber = (value: number | undefined, decimals: number = 1, unit: string = '') => {
    if (value === undefined || value === null) return `0${unit}`;
    return `${value.toFixed(decimals)}${unit}`;
  };

  const getChargeColor = (percent: number | undefined) => {
    if (percent === undefined || percent === null) return 'medium';
    if (percent >= 80) return 'high';
    if (percent >= 40) return 'medium';
    return 'low';
  };

  const getTemperatureColor = (temp: number | undefined) => {
    if (temp === undefined || temp === null) return 'medium';
    if (temp > 35) return 'high';
    if (temp < 15) return 'low';
    return 'medium';
  };

  // Ensure all values have defaults - handle undefined/null safely
  if (!telemetry) {
    return <div className="loading">Loading telemetry data...</div>;
  }

  const batteryCharge = telemetry.battery_charge_percent ?? 0;
  const batteryPower = telemetry.battery_power_kw ?? 0;
  const batteryTemp = telemetry.battery_temperature_c ?? 25;
  const stateOfHealth = telemetry.state_of_health ?? 100;
  const solarPower = telemetry.solar_power_kw ?? 0;
  const gridPower = telemetry.grid_power_kw ?? 0;
  const homePower = telemetry.home_power_kw ?? 0;
  const voltage = telemetry.voltage;
  const frequency = telemetry.frequency_hz;
  // Get operation mode and backup reserve from device config (more reliable)
  // Telemetry might be slightly stale, device config is always current
  const operationMode = device?.config?.operation_mode ?? telemetry?.operation_mode ?? 'self_powered';
  const backupReserve = device?.config?.backup_reserve_percent ?? telemetry?.backup_reserve_percent ?? 20;
  const timestamp = telemetry?.timestamp ?? new Date().toISOString();

  return (
    <div className="telemetry-overview">
      <div className="grid">
        <div className="card">
          <h3>Battery Status</h3>
          <div className="metric">
            <span className="metric-label">Charge Level</span>
            <span className={`metric-value ${getChargeColor(batteryCharge)}`}>
              {formatNumber(batteryCharge, 1, '%')}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Power</span>
            <span className={`metric-value ${batteryPower > 0.5 ? 'high' : batteryPower < -0.5 ? 'medium' : 'low'}`}>
              {batteryPower > 0.5 
                ? `+${formatNumber(batteryPower, 2, ' kW')} (Charging)`
                : batteryPower < -0.5
                ? `${formatNumber(batteryPower, 2, ' kW')} (Discharging)`
                : '0.00 kW (Idle)'}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Temperature</span>
            <span className={`metric-value ${getTemperatureColor(batteryTemp)}`}>
              {formatNumber(batteryTemp, 1, '°C')}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Health</span>
            <span className="metric-value medium">
              {formatNumber(stateOfHealth, 1, '%')}
            </span>
          </div>
          {telemetry?.cycles !== undefined && telemetry.cycles !== null && (
            <div className="metric">
              <span className="metric-label">Cycles</span>
              <span className="metric-value">{telemetry.cycles.toLocaleString()}</span>
            </div>
          )}
        </div>

        <div className="card">
          <h3>Solar Generation</h3>
          <div className="metric">
            <span className="metric-label">Current Power</span>
            <span className="metric-value high">
              {formatNumber(solarPower, 2, ' kW')}
            </span>
          </div>
          {device.solar_capacity_kw && (
            <div className="metric">
              <span className="metric-label">Capacity</span>
              <span className="metric-value">
                {device.solar_capacity_kw} kW
              </span>
            </div>
          )}
          <div className="metric">
            <span className="metric-label">Utilization</span>
            <span className="metric-value">
              {device.solar_capacity_kw && solarPower !== undefined
                ? formatNumber((solarPower / device.solar_capacity_kw) * 100, 1, '%')
                : '0%'}
            </span>
          </div>
        </div>

        <div className="card">
          <h3>Grid Interaction</h3>
          <div className="metric">
            <span className="metric-label">Grid Power</span>
            <span className={`metric-value ${Math.abs(gridPower) < 0.1 ? 'medium' : gridPower > 0 ? 'low' : 'high'}`}>
              {Math.abs(gridPower) < 0.1 ? '0.00 kW (Isolated)' : formatPower(gridPower)}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Status</span>
            <span className="metric-value">
              {Math.abs(gridPower) < 0.1 
                ? 'Isolated' 
                : gridPower > 0 
                ? 'Importing' 
                : 'Exporting'}
            </span>
          </div>
          {voltage !== undefined && voltage !== null && (
            <div className="metric">
              <span className="metric-label">Voltage</span>
              <span className="metric-value">
                {formatNumber(voltage, 1, ' V')}
              </span>
            </div>
          )}
          {frequency !== undefined && frequency !== null && (
            <div className="metric">
              <span className="metric-label">Frequency</span>
              <span className="metric-value">
                {formatNumber(frequency, 2, ' Hz')}
              </span>
            </div>
          )}
        </div>

        <div className="card">
          <h3>Home Consumption</h3>
          <div className="metric">
            <span className="metric-label">Current Power</span>
            <span className="metric-value">
              {formatNumber(homePower, 2, ' kW')}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Source</span>
            <span className="metric-value">
              {batteryPower < -0.5
                ? 'Battery'
                : solarPower > 0.5
                ? 'Solar'
                : 'Grid'}
            </span>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>System Configuration</h3>
        <div className="grid">
          <div className="metric">
            <span className="metric-label">Operation Mode</span>
            <span className="metric-value">
              {operationMode.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Backup Reserve</span>
            <span className="metric-value">
              {formatNumber(backupReserve, 0, '%')}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Firmware</span>
            <span className="metric-value">
              {device.firmware_version || 'Unknown'}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Last Update</span>
            <span className="metric-value">
              {timestamp ? new Date(timestamp).toLocaleTimeString() : 'Unknown'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TelemetryOverview;

