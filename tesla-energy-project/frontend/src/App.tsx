import React, { useState, useEffect } from 'react';
import './App.css';
import DeviceList from './components/DeviceList/DeviceList';
import Dashboard from './components/Dashboard/Dashboard';
import { Device } from './types/device';
import { deviceApi } from './services/api';

function App() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      setLoading(true);
      const response = await deviceApi.listDevices();
      setDevices(response.devices);
      if (response.devices.length > 0 && !selectedDevice) {
        setSelectedDevice(response.devices[0]);
      }
    } catch (error) {
      console.error('Error loading devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeviceUpdate = (updatedDevice: Device) => {
    // Update device in the devices list
    setDevices(devices.map(d => d.device_id === updatedDevice.device_id ? updatedDevice : d));
    
    // Update selected device if it's the one that changed
    if (selectedDevice && selectedDevice.device_id === updatedDevice.device_id) {
      setSelectedDevice(updatedDevice);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>Mock Tesla Energy Device Software Testing</h1>
          <p className="subtitle">Powerwall Telemetry Dashboard - Simulated Data</p>
        </div>
      </header>
      <main className="App-main">
        <div className="sidebar">
          <DeviceList
            devices={devices}
            selectedDevice={selectedDevice}
            onSelectDevice={setSelectedDevice}
            onRefresh={loadDevices}
            loading={loading}
          />
        </div>
        <div className="content">
          {selectedDevice ? (
            <Dashboard device={selectedDevice} onDeviceUpdate={handleDeviceUpdate} />
          ) : (
            <div className="no-device-selected">
              <h2>No Device Selected</h2>
              <p>Select a device from the sidebar to view its telemetry and controls.</p>
            </div>
          )}
        </div>
      </main>
      <footer className="App-footer">
        <div className="footer-content">
          <p><strong>Disclaimer:</strong> This is a <strong>mock/simulated project</strong> with <strong>fake, generated data</strong>. All telemetry, device states, and configurations are simulated and do not connect to real Tesla devices. This demonstration showcases software engineering capabilities for IoT energy management systems.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;

