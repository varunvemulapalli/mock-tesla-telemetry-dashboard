import React, { useState, useEffect } from 'react';
import { Device, Telemetry } from '../../types/device';
import { telemetryApi, deviceApi } from '../../services/api';
import { WebSocketService } from '../../services/websocket';
import TelemetryOverview from '../TelemetryOverview/TelemetryOverview';
import Charts from '../Charts/Charts';
import ControlPanel from '../ControlPanel/ControlPanel';
import HealthAnalysis from '../HealthAnalysis/HealthAnalysis';
import './Dashboard.css';

interface DashboardProps {
  device: Device;
  onDeviceUpdate?: (device: Device) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ device: initialDevice, onDeviceUpdate }) => {
  const [device, setDevice] = useState<Device>(initialDevice);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [loading, setLoading] = useState(true);
  const [wsService, setWsService] = useState<WebSocketService | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'control' | 'health'>('overview');

  // Refresh device data when switching tabs or device changes
  useEffect(() => {
    if (initialDevice.device_id !== device.device_id) {
      setDevice(initialDevice);
    }
  }, [initialDevice]);

  useEffect(() => {
    // Load initial telemetry and device data
    loadTelemetry();
    loadDevice();

    // Setup WebSocket connection
    const ws = new WebSocketService(device.device_id);
    ws.connect()
      .then(() => {
        setWsService(ws);
        const unsubscribe = ws.subscribe((data) => {
          setTelemetry(data);
          setLoading(false);
        });
        return unsubscribe;
      })
      .catch((error) => {
        console.error('WebSocket connection failed:', error);
        setLoading(false);
      });

    return () => {
      if (ws) {
        ws.disconnect();
      }
    };
  }, [device.device_id]);

  // Refresh device data periodically and when switching tabs
  useEffect(() => {
    // Refresh immediately when switching to overview or control
    if (activeTab === 'overview' || activeTab === 'control') {
      loadDevice();
      loadTelemetry();
    }
    
    const interval = setInterval(() => {
      if (activeTab === 'overview' || activeTab === 'control') {
        loadDevice();
        loadTelemetry();
      }
    }, 3000); // Refresh every 3 seconds for faster updates
    
    return () => clearInterval(interval);
  }, [activeTab, device.device_id]);

  const loadTelemetry = async () => {
    try {
      setLoading(true);
      const data = await telemetryApi.getLatest(device.device_id);
      setTelemetry(data);
    } catch (error) {
      console.error('Error loading telemetry:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDevice = async () => {
    try {
      const updatedDevice = await deviceApi.getDevice(device.device_id);
      setDevice(updatedDevice);
      if (onDeviceUpdate) {
        onDeviceUpdate(updatedDevice);
      }
    } catch (error) {
      console.error('Error loading device:', error);
    }
  };

  if (loading && !telemetry) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading device telemetry...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>{device.model}</h1>
          <p className="device-info">
            {device.device_id} {device.location && `• ${device.location}`}
          </p>
        </div>
        <div className="device-status-badge">
          <span
            className={`status-indicator ${
              device.status === 'online' || device.status === 'charging' || device.status === 'discharging'
                ? 'online'
                : 'offline'
            }`}
          >
            ●
          </span>
          {device.status}
        </div>
      </div>

      <div className="dashboard-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'charts' ? 'active' : ''}`}
          onClick={() => setActiveTab('charts')}
        >
          Charts
        </button>
        <button
          className={`tab ${activeTab === 'control' ? 'active' : ''}`}
          onClick={() => setActiveTab('control')}
        >
          Control
        </button>
        <button
          className={`tab ${activeTab === 'health' ? 'active' : ''}`}
          onClick={() => setActiveTab('health')}
        >
          Health Analysis
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === 'overview' && telemetry && (
          <TelemetryOverview device={device} telemetry={telemetry} key={`${device.device_id}-${device.config.operation_mode}-${device.status}`} />
        )}
        {activeTab === 'charts' && (
          <Charts device={device} />
        )}
        {activeTab === 'control' && (
          <ControlPanel device={device} onCommandExecuted={loadDevice} />
        )}
        {activeTab === 'health' && (
          <HealthAnalysis device={device} />
        )}
      </div>
    </div>
  );
};

export default Dashboard;

