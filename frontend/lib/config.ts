/**
 * Application configuration
 */

export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
} as const;

/**
 * API endpoints
 */
export const endpoints = {
  metrics: {
    history: '/api/metrics/history',
    latest: '/api/metrics/latest',
  },
  insights: {
    optimize: '/api/insights/optimize',
  },
  websocket: {
    telemetry: '/ws/telemetry',
  },
} as const;

/**
 * Default optimization parameters
 */
export const defaultOptimizationParams = {
  analysis_hours: 24,
  min_shutdown_hours: 2,
  max_shutdown_hours: 8,
} as const;
