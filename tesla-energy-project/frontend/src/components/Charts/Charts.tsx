import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { Device, Telemetry } from '../../types/device';
import { telemetryApi } from '../../services/api';
import './Charts.css';

interface ChartsProps {
  device: Device;
}

const Charts: React.FC<ChartsProps> = ({ device }) => {
  const [history, setHistory] = useState<Telemetry[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<number>(24);

  useEffect(() => {
    loadHistory();
  }, [device.device_id, timeRange]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const endTime = new Date();
      // Scale: 1 minute real time = 1 hour simulation time
      // So timeRange hours of simulation = timeRange minutes of real time
      const startTime = new Date(endTime.getTime() - timeRange * 60 * 1000);
      const data = await telemetryApi.getHistory(device.device_id, startTime, endTime, 200);
      setHistory(data.data_points || []);
    } catch (error) {
      console.error('Error loading history:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading chart data...</div>;
  }

  if (history.length === 0) {
    return <div className="no-data">No historical data available</div>;
  }

  // Sort history by timestamp to ensure chronological order
  const sortedHistory = [...history].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  
  // Transform timestamps to show simulation time scale
  // Scale: 1 minute real time = 1 hour simulation time
  // We transform timestamps so each data point appears 1 hour apart on the chart
  // Find the most recent timestamp as the baseline
  const mostRecentTime = sortedHistory.length > 0 
    ? new Date(sortedHistory[sortedHistory.length - 1].timestamp).getTime()
    : Date.now();
  
  // Transform each timestamp: calculate minutes from most recent, then scale to hours
  const timestamps = sortedHistory.map((t, index) => {
    const actualTime = new Date(t.timestamp).getTime();
    // Calculate minutes since most recent point (this represents hours in simulation)
    const minutesFromNow = (mostRecentTime - actualTime) / (60 * 1000);
    // Scale: 1 minute real = 1 hour sim, so minutesFromNow = simulated hours ago
    // Create display timestamp that is 'simulated hours ago' hours before now
    const now = new Date();
    const displayTime = new Date(now.getTime() - minutesFromNow * 60 * 60 * 1000);
    return displayTime;
  });
  
  // Update data arrays to use sorted history
  const batteryCharge = sortedHistory.map((t) => t.battery_charge_percent ?? 0);
  const solarPower = sortedHistory.map((t) => t.solar_power_kw ?? 0);
  const homePower = sortedHistory.map((t) => t.home_power_kw ?? 0);
  const gridPower = sortedHistory.map((t) => t.grid_power_kw ?? 0);
  const batteryPower = sortedHistory.map((t) => t.battery_power_kw ?? 0);
  const temperature = sortedHistory.map((t) => t.battery_temperature_c ?? 25);

  // Format time range label
  const getTimeRangeLabel = (hours: number) => {
    if (hours < 24) {
      return `${hours} ${hours === 1 ? 'Hour' : 'Hours'}`;
    } else {
      const days = hours / 24;
      return `${days} ${days === 1 ? 'Day' : 'Days'}`;
    }
  };

  // Calculate appropriate tick format and interval based on time range
  // Since 1 minute real = 1 hour sim, we need to format accordingly
  const getTickFormat = () => {
    // Format based on time range - show hours for simulation time
    if (timeRange <= 6) {
      return '%H:%M'; // Show hours:minutes (e.g., "14:30")
    } else if (timeRange <= 24) {
      return '%H:%M'; // Show hours:minutes
    } else {
      return '%m/%d %H:%M'; // Show date and time for longer ranges
    }
  };

  const getTickInterval = () => {
    // Timestamps are transformed: 1 minute real time = 1 hour simulated time
    // Display timestamps show real time, where each hour represents 1 simulated hour
    // dtick is in milliseconds for the display timestamps (real time)
    // For 6 hours: each tick = 1 hour simulated = 1 hour display = 3600000ms
    // For 24 hours: each tick = 4 hours simulated = 4 hours display = 14400000ms
    // For 48 hours: 6 ticks of 8 hours each = 48 hours total = 28800000ms per tick
    // For 7 days (168 hours): 6 ticks of 28 hours each = 168 hours total = 100800000ms per tick
    if (timeRange <= 6) {
      return 3600000; // 1 hour = 1 hour simulated
    } else if (timeRange <= 24) {
      return 14400000; // 4 hours = 4 hours simulated
    } else if (timeRange <= 48) {
      return 28800000; // 8 hours per tick, 6 ticks total = 48 hours
    } else {
      return 100800000; // 28 hours per tick, 6 ticks total = 168 hours
    }
  };

  const getXAxisRange = () => {
    if (sortedHistory.length === 0) return undefined;
    
    // For all time ranges, ensure range spans exactly the time range
    // This ensures exactly 6 ticks are shown
    // 6 hours: 6 ticks of 1 hour each
    // 24 hours: 6 ticks of 4 hours each
    // 48 hours: 6 ticks of 8 hours each
    // 7 days (168 hours): 6 ticks of 28 hours each
    const rangeMs = timeRange * 60 * 60 * 1000; // Convert hours to ms (display time)
    const now = new Date();
    return [new Date(now.getTime() - rangeMs), now];
  };

  const baseLayout = {
    paper_bgcolor: '#1a1f3a',
    plot_bgcolor: '#0f1425',
    font: { color: '#ffffff', size: 12 },
    xaxis: {
      gridcolor: '#2a2f4a',
      showgrid: true,
      tickformat: getTickFormat(),
      dtick: getTickInterval(),
      range: getXAxisRange(),
      title: `Time (Simulated Hours)`,
      tickangle: -45,
    } as any,
    yaxis: {
      gridcolor: '#2a2f4a',
      showgrid: true,
    },
    legend: {
      bgcolor: 'transparent',
      font: { color: '#ffffff' },
    },
    margin: { l: 60, r: 30, t: 30, b: 90 },
  };

  return (
    <div className="charts">
      <div className="charts-controls">
        <div>
          <h2>Historical Data</h2>
          <p style={{ fontSize: '0.85rem', color: '#a0a0a0', marginTop: '0.25rem', marginBottom: 0 }}>
            Simulation Time: 1 minute real time = 1 hour simulated time • Data points represent hourly intervals
            <br />
            Example: 5:00-6:00 p.m. on the Chart reflects 1 minute of live waiting 
          </p>
        </div>
        <div className="time-range-selector">
          <button
            className={timeRange === 6 ? 'active' : ''}
            onClick={() => setTimeRange(6)}
          >
            6 Hours
          </button>
          <button
            className={timeRange === 24 ? 'active' : ''}
            onClick={() => setTimeRange(24)}
          >
            24 Hours
          </button>
          <button
            className={timeRange === 48 ? 'active' : ''}
            onClick={() => setTimeRange(48)}
          >
            48 Hours
          </button>
          <button
            className={timeRange === 168 ? 'active' : ''}
            onClick={() => setTimeRange(168)}
          >
            7 Days
          </button>
        </div>
      </div>

      <div className="chart-container">
        <div className="card">
          <h3>Battery Charge Level</h3>
          <Plot
            data={[
              {
                x: timestamps,
                y: batteryCharge,
                type: 'scatter',
                mode: 'lines',
                name: 'Battery Charge %',
                line: { color: '#3b82f6', width: 2 },
                fill: 'tozeroy',
                fillcolor: 'rgba(59, 130, 246, 0.1)',
              },
            ]}
            layout={{
              ...baseLayout,
              title: '',
              yaxis: { ...baseLayout.yaxis, title: 'Charge (%)', range: [0, 100] },
            }}
            style={{ width: '100%', height: '400px' }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
      </div>

      <div className="chart-container">
        <div className="card">
          <h3>Power Flow (kW)</h3>
          <Plot
            data={[
              {
                x: timestamps,
                y: solarPower,
                type: 'scatter',
                mode: 'lines',
                name: 'Solar',
                line: { color: '#f59e0b', width: 2 },
              },
              {
                x: timestamps,
                y: homePower,
                type: 'scatter',
                mode: 'lines',
                name: 'Home',
                line: { color: '#ef4444', width: 2 },
              },
              {
                x: timestamps,
                y: batteryPower,
                type: 'scatter',
                mode: 'lines',
                name: 'Battery',
                line: { color: '#3b82f6', width: 2 },
              },
              {
                x: timestamps,
                y: gridPower,
                type: 'scatter',
                mode: 'lines',
                name: 'Grid',
                line: { color: '#10b981', width: 2, dash: 'dash' },
              },
            ]}
            layout={{
              ...baseLayout,
              title: '',
              yaxis: { ...baseLayout.yaxis, title: 'Power (kW)' },
            }}
            style={{ width: '100%', height: '400px' }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
      </div>

      <div className="chart-container">
        <div className="card">
          <h3>Battery Temperature</h3>
          <Plot
            data={[
              {
                x: timestamps,
                y: temperature,
                type: 'scatter',
                mode: 'lines',
                name: 'Temperature',
                line: { color: '#ef4444', width: 2 },
                fill: 'tozeroy',
                fillcolor: 'rgba(239, 68, 68, 0.1)',
              },
            ]}
            layout={{
              ...baseLayout,
              title: '',
              yaxis: { ...baseLayout.yaxis, title: 'Temperature (°C)' },
            }}
            style={{ width: '100%', height: '400px' }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
      </div>
    </div>
  );
};

export default Charts;

