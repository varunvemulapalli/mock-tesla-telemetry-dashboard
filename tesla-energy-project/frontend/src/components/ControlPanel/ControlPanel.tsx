import React, { useState } from 'react';
import { Device, ControlCommandType } from '../../types/device';
import { controlApi, deviceApi } from '../../services/api';
import './ControlPanel.css';

interface ControlPanelProps {
  device: Device;
  onCommandExecuted?: () => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ device: initialDevice, onCommandExecuted }) => {
  const [device, setDevice] = useState<Device>(initialDevice);
  const [loading, setLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [backupReserve, setBackupReserve] = useState(initialDevice.config.backup_reserve_percent);
  const [operationMode, setOperationMode] = useState(initialDevice.config.operation_mode);

  // Update local state when device prop changes
  React.useEffect(() => {
    setDevice(initialDevice);
    setBackupReserve(initialDevice.config.backup_reserve_percent);
    setOperationMode(initialDevice.config.operation_mode);
  }, [initialDevice]);

  const executeCommand = async (command: ControlCommandType, parameters?: Record<string, any>) => {
    try {
      setLoading(command);
      setMessage(null);
      const result = await controlApi.executeCommand(device.device_id, {
        command,
        parameters,
      });
      
      // Refresh device data to get updated state
      const updatedDevice = await deviceApi.getDevice(device.device_id);
      setDevice(updatedDevice);
      
      // Extract message from result (ensure it's a string)
      const resultMessage = result?.message 
        ? (typeof result.message === 'string' ? result.message : String(result.message))
        : 'Command executed successfully';
      
      // Update local state if config changed
      if (resultMessage.includes('Backup reserve')) {
        setBackupReserve(updatedDevice.config.backup_reserve_percent);
      }
      if (resultMessage.includes('Operation mode')) {
        setOperationMode(updatedDevice.config.operation_mode);
      }
      
      setMessage({ type: 'success', text: resultMessage });
      setTimeout(() => setMessage(null), 5000);
      
      // Notify parent to refresh
      if (onCommandExecuted) {
        onCommandExecuted();
      }
    } catch (error: any) {
      console.error('Command error:', error);
      
      // Extract error message from FastAPI validation errors
      let errorMessage = 'Command failed';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Handle FastAPI validation errors (422)
        if (errorData.detail && Array.isArray(errorData.detail)) {
          // Validation errors are in array format
          const errors = errorData.detail.map((e: any) => {
            const loc = Array.isArray(e.loc) ? e.loc.join('.') : '';
            return `${loc}: ${e.msg}`;
          }).join(', ');
          errorMessage = `Validation error: ${errors}`;
        } else if (errorData.detail && typeof errorData.detail === 'string') {
          // Single error message
          errorMessage = errorData.detail;
        } else if (typeof errorData.detail === 'object') {
          // Error object - extract message
          errorMessage = JSON.stringify(errorData.detail);
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setMessage({
        type: 'error',
        text: errorMessage,
      });
      setTimeout(() => setMessage(null), 5000);
    } finally {
      setLoading(null);
    }
  };

  const handleBackupReserveChange = async () => {
    await executeCommand(ControlCommandType.SET_BACKUP_RESERVE, {
      percent: backupReserve,
    });
  };

  return (
    <div className="control-panel">
      {message && message.text && (
        <div className={message.type === 'success' ? 'success' : 'error'}>
          {String(message.text)}
        </div>
      )}

      <div className="card">
        <h2>Device Control</h2>
        <p className="control-description">
          Execute commands to control your {device.model}. Changes may take a few moments to apply.
        </p>

        <div className="control-section">
          <h3>Battery Control</h3>
          <div className="control-buttons">
            <button
              className="button"
              onClick={() => executeCommand(ControlCommandType.CHARGE_NOW)}
              disabled={loading !== null || device.status === 'offline' || device.status === 'charging'}
            >
              {loading === ControlCommandType.CHARGE_NOW 
                ? 'Starting...' 
                : device.status === 'charging'
                ? 'Charging (Active)'
                : 'Charge Now'}
            </button>
            <button
              className="button button-secondary"
              onClick={() => executeCommand(ControlCommandType.STOP_CHARGING)}
              disabled={loading !== null || device.status === 'offline' || device.status !== 'charging'}
            >
              {loading === ControlCommandType.STOP_CHARGING 
                ? 'Stopping...' 
                : 'Stop Charging'}
            </button>
          </div>
          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#a0a0a0' }}>
            {device.status === 'charging' 
              ? 'Battery is currently charging. Click "Stop Charging" to return to normal operation.'
              : 'Click "Charge Now" to force battery charging for 30 minutes or until full.'}
          </div>
        </div>

        <div className="control-section">
          <h3>Grid Control</h3>
          <div className="control-buttons">
            <button
              className="button button-secondary"
              onClick={() => executeCommand(ControlCommandType.ISOLATE_FROM_GRID)}
              disabled={loading !== null || device.status === 'offline'}
            >
              {loading === ControlCommandType.ISOLATE_FROM_GRID
                ? 'Isolating...'
                : 'Isolate from Grid'}
            </button>
            <button
              className="button button-secondary"
              onClick={() => executeCommand(ControlCommandType.REJOIN_GRID)}
              disabled={loading !== null || device.status === 'offline'}
            >
              {loading === ControlCommandType.REJOIN_GRID ? 'Rejoining...' : 'Rejoin Grid'}
            </button>
            <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#a0a0a0' }}>
              When isolated, battery supplies all home power. Grid power will be zero.
            </div>
          </div>
        </div>

        <div className="control-section">
          <h3>System Control</h3>
          <div className="control-buttons">
            <button
              className="button button-secondary"
              onClick={() => executeCommand(ControlCommandType.REBOOT)}
              disabled={loading !== null || device.status === 'offline'}
            >
              {loading === ControlCommandType.REBOOT ? 'Rebooting...' : 'Reboot Device'}
            </button>
            <button
              className="button button-secondary"
              onClick={() =>
                executeCommand(ControlCommandType.FIRMWARE_UPDATE, {
                  version: '23.45.0',
                })
              }
              disabled={loading !== null || device.status === 'offline'}
            >
              {loading === ControlCommandType.FIRMWARE_UPDATE
                ? 'Updating...'
                : 'Update Firmware'}
            </button>
          </div>
        </div>

        <div className="control-section">
          <h3>Configuration</h3>
          <div className="config-item">
            <label htmlFor="backup-reserve">Backup Reserve: {backupReserve}%</label>
            <input
              id="backup-reserve"
              type="range"
              min="0"
              max="100"
              value={backupReserve}
              onChange={(e) => setBackupReserve(Number(e.target.value))}
              className="slider"
            />
            <button
              className="button"
              onClick={handleBackupReserveChange}
              disabled={loading !== null || device.status === 'offline'}
            >
              Update Backup Reserve
            </button>
          </div>

          <div className="config-item">
            <label>Operation Mode</label>
            <select
              className="select"
              value={operationMode}
              onChange={(e) => {
                setOperationMode(e.target.value as any);
                executeCommand(ControlCommandType.SET_OPERATION_MODE, {
                  mode: e.target.value,
                });
              }}
              disabled={loading !== null || device.status === 'offline'}
            >
              <option value="backup">Backup Only</option>
              <option value="self_powered">Self-Powered</option>
              <option value="time_based_control">Time-Based Control</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Command History</h2>
        <CommandHistory deviceId={device.device_id} />
      </div>
    </div>
  );
};

const CommandHistory: React.FC<{ deviceId: string }> = ({ deviceId }) => {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    loadHistory();
    const interval = setInterval(loadHistory, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [deviceId]);

  const loadHistory = async () => {
    try {
      const data = await controlApi.getCommandHistory(deviceId, 10);
      setHistory(data.commands || []);
    } catch (error) {
      console.error('Error loading command history:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading command history...</div>;
  }

  if (history.length === 0) {
    return <div className="no-history">No commands executed yet</div>;
  }

  return (
    <div className="command-history">
      {history.map((cmd, index) => (
        <div key={index} className="command-item">
          <div className="command-header">
            <span className="command-type">{cmd.command.replace(/_/g, ' ')}</span>
            <span className="command-time">
              {new Date(cmd.timestamp).toLocaleString()}
            </span>
          </div>
          {cmd.parameters && Object.keys(cmd.parameters).length > 0 && (
            <div className="command-params">
              {JSON.stringify(cmd.parameters)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ControlPanel;

