/**
 * Example usage of the API Client
 * This file demonstrates how to use the apiClient singleton
 */

import { apiClient } from './api-client';

/**
 * Example: Fetch historical data for the last 24 hours
 */
export async function fetchLast24Hours() {
  const end = new Date();
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
  
  try {
    const data = await apiClient.getHistoricalData(start, end);
    console.log(`Fetched ${data.length} telemetry readings`);
    return data;
  } catch (error) {
    console.error('Failed to fetch historical data:', error);
    throw error;
  }
}

/**
 * Example: Get the latest reading
 */
export async function fetchLatestMetrics() {
  try {
    const reading = await apiClient.getLatestReading();
    console.log('Latest reading:', reading);
    return reading;
  } catch (error) {
    console.error('Failed to fetch latest reading:', error);
    throw error;
  }
}

/**
 * Example: Request optimization with default parameters
 */
export async function requestOptimization() {
  try {
    const result = await apiClient.requestOptimization();
    console.log('Optimization result:', result);
    return result;
  } catch (error) {
    console.error('Failed to request optimization:', error);
    throw error;
  }
}

/**
 * Example: Request optimization with custom parameters
 */
export async function requestCustomOptimization() {
  try {
    const result = await apiClient.requestOptimization({
      analysis_hours: 48,
      min_shutdown_hours: 3,
      max_shutdown_hours: 6,
    });
    console.log('Custom optimization result:', result);
    return result;
  } catch (error) {
    console.error('Failed to request custom optimization:', error);
    throw error;
  }
}

/**
 * Example: Check backend health
 */
export async function checkBackendHealth() {
  try {
    const isHealthy = await apiClient.healthCheck();
    console.log('Backend health:', isHealthy ? 'OK' : 'DOWN');
    return isHealthy;
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
}
