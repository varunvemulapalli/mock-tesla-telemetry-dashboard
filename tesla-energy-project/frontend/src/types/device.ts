export enum DeviceType {
  POWERWALL = "powerwall",
  SOLAR_INVERTER = "solar_inverter",
  WALL_CONNECTOR = "wall_connector",
}

export enum DeviceStatus {
  ONLINE = "online",
  OFFLINE = "offline",
  STANDBY = "standby",
  CHARGING = "charging",
  DISCHARGING = "discharging",
  FAULT = "fault",
  UPDATING = "updating",
}

export enum OperationMode {
  BACKUP = "backup",
  SELF_POWERED = "self_powered",
  TIME_BASED_CONTROL = "time_based_control",
  ADVANCED = "advanced",
}

export enum ControlCommandType {
  CHARGE_NOW = "charge_now",
  STOP_CHARGING = "stop_charging",
  ISOLATE_FROM_GRID = "isolate_from_grid",
  REJOIN_GRID = "rejoin_grid",
  REBOOT = "reboot",
  FIRMWARE_UPDATE = "firmware_update",
  SET_BACKUP_RESERVE = "set_backup_reserve",
  SET_OPERATION_MODE = "set_operation_mode",
}

export interface DeviceConfig {
  backup_reserve_percent: number;
  operation_mode: OperationMode;
  grid_charging_enabled: boolean;
  storm_watch_enabled: boolean;
  time_of_use_enabled: boolean;
  firmware_version: string;
  installation_date?: string;
}

export interface Device {
  device_id: string;
  serial_number: string;
  device_type: DeviceType;
  model: string;
  firmware_version: string;
  status: DeviceStatus;
  config: DeviceConfig;
  location?: string;
  installed_at: string;
  last_seen: string;
  battery_capacity_kwh: number;
  solar_capacity_kw?: number;
}

export interface Telemetry {
  device_id: string;
  timestamp: string;
  battery_charge_percent: number;
  battery_power_kw: number;
  solar_power_kw: number;
  grid_power_kw: number;
  home_power_kw: number;
  battery_temperature_c: number;
  inverter_temperature_c?: number;
  voltage?: number;
  frequency_hz?: number;
  state_of_health: number;
  cycles?: number;
  backup_reserve_percent: number;
  operation_mode: string;
}

export interface ControlCommand {
  command: ControlCommandType;
  parameters?: Record<string, any>;
  timestamp?: string;
}

export interface HealthAnalysis {
  device_id: string;
  overall_health_score: number;
  analysis: string;
  recommendations: string[];
  key_metrics: Record<string, any>;
  timestamp: string;
}

export interface DeviceListResponse {
  devices: Device[];
  total: number;
  page: number;
  page_size: number;
}

