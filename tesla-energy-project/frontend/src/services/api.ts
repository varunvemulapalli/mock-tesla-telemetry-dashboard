import axios from 'axios';
import {
  Device,
  DeviceListResponse,
  Telemetry,
  ControlCommand,
  DeviceConfig,
  HealthAnalysis,
} from '../types/device';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const deviceApi = {
  listDevices: async (page = 1, pageSize = 50): Promise<DeviceListResponse> => {
    const response = await api.get<DeviceListResponse>('/api/devices', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getDevice: async (deviceId: string): Promise<Device> => {
    const response = await api.get<Device>(`/api/devices/${deviceId}`);
    return response.data;
  },

  updateDeviceConfig: async (
    deviceId: string,
    config: DeviceConfig
  ): Promise<Device> => {
    const response = await api.put<Device>(`/api/devices/${deviceId}/config`, config);
    return response.data;
  },

  getDeviceStatus: async (deviceId: string): Promise<any> => {
    const response = await api.get(`/api/devices/${deviceId}/status`);
    return response.data;
  },
};

export const telemetryApi = {
  getLatest: async (deviceId: string): Promise<Telemetry> => {
    const response = await api.get<Telemetry>(`/api/telemetry/${deviceId}`);
    return response.data;
  },

  getHistory: async (
    deviceId: string,
    startTime?: Date,
    endTime?: Date,
    limit = 100
  ): Promise<any> => {
    const params: any = { limit };
    if (startTime) params.start_time = startTime.toISOString();
    if (endTime) params.end_time = endTime.toISOString();
    const response = await api.get(`/api/telemetry/${deviceId}/history`, { params });
    return response.data;
  },

  getAnalytics: async (deviceId: string, hours = 24): Promise<any> => {
    const response = await api.get(`/api/telemetry/${deviceId}/analytics`, {
      params: { hours },
    });
    return response.data;
  },
};

export const controlApi = {
  executeCommand: async (
    deviceId: string,
    command: ControlCommand
  ): Promise<any> => {
    // Send only the command and parameters (timestamp is optional)
    const payload: any = {
      command: command.command,
    };
    if (command.parameters) {
      payload.parameters = command.parameters;
    }
    
    const response = await api.post(`/api/control/${deviceId}`, payload);
    return response.data;
  },

  getCommandHistory: async (deviceId: string, limit = 50): Promise<any> => {
    const response = await api.get(`/api/control/${deviceId}/history`, {
      params: { limit },
    });
    return response.data;
  },
};

export const healthApi = {
  analyze: async (
    deviceId: string,
    analysisType = 'comprehensive',
    includeRecommendations = true
  ): Promise<HealthAnalysis> => {
    const response = await api.post<HealthAnalysis>('/api/health/analyze', {
      device_id: deviceId,
      analysis_type: analysisType,
      include_recommendations: includeRecommendations,
    });
    return response.data;
  },

  getSummary: async (deviceId: string): Promise<any> => {
    const response = await api.get(`/api/health/${deviceId}/summary`);
    return response.data;
  },
};

export default api;

