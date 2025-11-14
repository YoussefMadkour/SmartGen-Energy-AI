/**
 * API Client for Energy Optimization ROI Dashboard
 * Handles all HTTP communication with the backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { config, endpoints, defaultOptimizationParams } from './config';
import type {
  TelemetryReading,
  OptimizationResult,
  OptimizationParams,
  APIError,
} from '../types';

/**
 * Custom error class for API errors
 */
export class APIClientError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'APIClientError';
  }
}

/**
 * API Client class for backend communication
 */
class APIClient {
  private axiosInstance: AxiosInstance;
  private readonly maxRetries = 3;
  private readonly retryDelay = 1000; // 1 second

  constructor(baseURL: string) {
    this.axiosInstance = axios.create({
      baseURL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error: AxiosError<APIError>) => {
        return this.handleError(error);
      }
    );
  }

  /**
   * Handle API errors with user-friendly messages
   */
  private handleError(error: AxiosError<APIError>): Promise<never> {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      const message = data?.error || 'An error occurred';
      const detail = data?.detail || error.message;

      throw new APIClientError(message, status, detail);
    } else if (error.request) {
      // Request made but no response received
      throw new APIClientError(
        'Unable to reach the server. Please check your connection.',
        undefined,
        'Network error'
      );
    } else {
      // Error setting up the request
      throw new APIClientError(
        'Failed to make request',
        undefined,
        error.message
      );
    }
  }

  /**
   * Retry logic for transient failures
   */
  private async retryRequest<T>(
    requestFn: () => Promise<T>,
    retries = this.maxRetries
  ): Promise<T> {
    try {
      return await requestFn();
    } catch (error) {
      if (retries > 0 && this.isRetryableError(error)) {
        await this.delay(this.retryDelay);
        return this.retryRequest(requestFn, retries - 1);
      }
      throw error;
    }
  }

  /**
   * Check if error is retryable (network errors, 5xx errors)
   */
  private isRetryableError(error: unknown): boolean {
    if (error instanceof APIClientError) {
      // Retry on server errors (5xx) or no status code (network errors)
      return !error.statusCode || error.statusCode >= 500;
    }
    return false;
  }

  /**
   * Delay helper for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Get historical telemetry data for a time range
   * @param start - Start date/time
   * @param end - End date/time
   * @returns Array of telemetry readings
   */
  async getHistoricalData(
    start: Date,
    end: Date
  ): Promise<TelemetryReading[]> {
    return this.retryRequest(async () => {
      const response = await this.axiosInstance.get<TelemetryReading[]>(
        endpoints.metrics.history,
        {
          params: {
            start: start.toISOString(),
            end: end.toISOString(),
          },
        }
      );
      return response.data;
    });
  }

  /**
   * Get the latest telemetry reading
   * @returns Most recent telemetry reading
   */
  async getLatestReading(): Promise<TelemetryReading> {
    return this.retryRequest(async () => {
      const response = await this.axiosInstance.get<TelemetryReading>(
        endpoints.metrics.latest
      );
      return response.data;
    });
  }

  /**
   * Request optimization analysis from the AI agent
   * @param params - Optimization parameters (optional)
   * @returns Optimization result with shutdown window and savings
   */
  async requestOptimization(
    params?: OptimizationParams
  ): Promise<OptimizationResult> {
    // Merge with default parameters
    const requestParams = {
      ...defaultOptimizationParams,
      ...params,
    };

    // No retry for optimization requests (they can be expensive)
    const response = await this.axiosInstance.post<OptimizationResult>(
      endpoints.insights.optimize,
      requestParams
    );
    return response.data;
  }

  /**
   * Health check endpoint (optional utility)
   * @returns true if backend is healthy
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.axiosInstance.get('/health');
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * Singleton instance of the API client
 * Export this for use across components
 */
export const apiClient = new APIClient(config.apiUrl);

/**
 * Export the class for testing purposes
 */
export { APIClient };
