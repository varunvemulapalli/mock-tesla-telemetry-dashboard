import React, { useState, useEffect } from 'react';
import { Device, DeviceStatus, Telemetry } from '../../types/device';
import { telemetryApi } from '../../services/api';
import './DeviceList.css';

interface DeviceListProps {
  devices: Device[];
  selectedDevice: Device | null;
  onSelectDevice: (device: Device) => void;
  onRefresh: () => void;
  loading: boolean;
}

const DeviceList: React.FC<DeviceListProps> = ({
  devices,
  selectedDevice,
  onSelectDevice,
  onRefresh,
  loading,
}) => {
  const [deviceTelemetry, setDeviceTelemetry] = useState<Map<string, Telemetry>>(new Map());

  // Load telemetry for all devices periodically
  useEffect(() => {
    const loadTelemetry = async () => {
      for (const device of devices) {
        try {
          const telemetry = await telemetryApi.getLatest(device.device_id);
          setDeviceTelemetry(prev => new Map(prev).set(device.device_id, telemetry));
        } catch (error) {
          console.error(`Error loading telemetry for ${device.device_id}:`, error);
        }
      }
    };

    loadTelemetry();
    const interval = setInterval(loadTelemetry, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, [devices]);

  const getStatusColor = (status: DeviceStatus) => {
    switch (status) {
      case DeviceStatus.ONLINE:
      case DeviceStatus.CHARGING:
      case DeviceStatus.DISCHARGING:
        return '#10b981';
      case DeviceStatus.STANDBY:
        return '#f59e0b';
      case DeviceStatus.OFFLINE:
      case DeviceStatus.FAULT:
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div className="device-list">
        <div className="device-list-header">
          <h2>Devices</h2>
          <button className="refresh-button" onClick={onRefresh} disabled>
            ↻
          </button>
        </div>
        <div className="loading">Loading devices...</div>
      </div>
    );
  }

  return (
    <div className="device-list">
      <div className="device-list-header">
        <h2>Devices</h2>
        <button className="refresh-button" onClick={onRefresh} title="Refresh">
          ↻
        </button>
      </div>
      {devices.length === 0 ? (
        <div className="no-devices">No devices found</div>
      ) : (
        <div className="device-items">
          {devices.map((device) => (
            <div
              key={device.device_id}
              className={`device-item ${
                selectedDevice?.device_id === device.device_id ? 'selected' : ''
              }`}
              onClick={() => onSelectDevice(device)}
            >
              <div className="device-item-header">
                <div className="device-name">{device.model}</div>
                <div
                  className="device-status"
                  style={{ color: getStatusColor(device.status) }}
                >
                  ● {device.status}
                </div>
              </div>
              <div className="device-id">{device.device_id}</div>
              {device.location && (
                <div className="device-location">{device.location}</div>
              )}
              {device.device_type === 'powerwall' && (
                <div className="device-capacity">
                  {deviceTelemetry.get(device.device_id)?.battery_charge_percent?.toFixed(1) ?? 'N/A'}% • {device.battery_capacity_kwh} kWh
                  {device.solar_capacity_kw && ` • ${device.solar_capacity_kw} kW Solar`}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DeviceList;

