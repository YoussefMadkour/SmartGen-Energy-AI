/**
 * Core data types for the Energy Optimization ROI Dashboard
 */

/**
 * Telemetry reading from the generator
 */
export interface TelemetryReading {
  id?: number;
  timestamp: string;
  power_load_kw: number;
  fuel_consumption_lph: number;
  status: 'ON' | 'OFF';
}

/**
 * Shutdown window recommendation
 */
export interface ShutdownWindow {
  start: string;
  end: string;
  duration_hours: number;
}

/**
 * Projected savings from optimization
 */
export interface Savings {
  daily_savings_usd: number;
  monthly_savings_usd: number;
  fuel_saved_liters: number;
}

/**
 * Complete optimization result from the AI agent
 */
export interface OptimizationResult {
  shutdown_window: ShutdownWindow;
  savings: Savings;
  recommendation: string;
}

/**
 * Parameters for requesting optimization
 */
export interface OptimizationParams {
  analysis_hours?: number;
  min_shutdown_hours?: number;
  max_shutdown_hours?: number;
}

/**
 * WebSocket message types
 */
export interface WebSocketMessage {
  type: 'telemetry' | 'error' | 'connected';
  data?: TelemetryReading | string;
}

/**
 * API error response
 */
export interface APIError {
  error: string;
  detail: string;
  timestamp: string;
}

/**
 * Time range options for historical data
 */
export type TimeRange = '6h' | '12h' | '24h';

/**
 * Dashboard state
 */
export interface DashboardState {
  liveMetrics: TelemetryReading | null;
  historicalData: TelemetryReading[];
  timeRange: TimeRange;
  optimization: OptimizationResult | null;
  isOptimizing: boolean;
  wsConnected: boolean;
}
