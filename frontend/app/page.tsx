'use client';

/**
 * Main Dashboard Page
 * Displays live generator metrics, historical charts, and AI-powered optimization recommendations
 */

import { useEffect, useState, useCallback } from 'react';
import { PowerLoadChart, FuelConsumptionChart, ROICard } from '@/components';
import { apiClient } from '@/lib/api-client';
import { telemetryWebSocket, ConnectionStatus } from '@/lib/websocket-client';
import type { TelemetryReading, OptimizationResult, TimeRange } from '@/types';

export default function DashboardPage() {
  // State management
  const [liveMetrics, setLiveMetrics] = useState<TelemetryReading | null>(null);
  const [historicalData, setHistoricalData] = useState<TelemetryReading[]>([]);
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');
  const [optimization, setOptimization] = useState<OptimizationResult | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  /**
   * Fetch historical data based on selected time range
   */
  const fetchHistoricalData = useCallback(async () => {
    try {
      setIsLoadingHistory(true);
      setError(null);

      // Calculate time range
      const end = new Date();
      const start = new Date();
      
      switch (timeRange) {
        case '6h':
          start.setHours(start.getHours() - 6);
          break;
        case '12h':
          start.setHours(start.getHours() - 12);
          break;
        case '24h':
          start.setHours(start.getHours() - 24);
          break;
      }

      const data = await apiClient.getHistoricalData(start, end);
      setHistoricalData(data);
    } catch (err) {
      console.error('Failed to fetch historical data:', err);
      setError('Failed to load historical data. Please try again.');
    } finally {
      setIsLoadingHistory(false);
    }
  }, [timeRange]);

  /**
   * Handle optimization request
   */
  const handleOptimize = async () => {
    try {
      setIsOptimizing(true);
      setError(null);

      const result = await apiClient.requestOptimization({
        analysis_hours: 24,
        min_shutdown_hours: 2,
        max_shutdown_hours: 8,
      });

      setOptimization(result);
    } catch (err) {
      console.error('Optimization failed:', err);
      setError('Failed to generate optimization. Please try again.');
    } finally {
      setIsOptimizing(false);
    }
  };

  /**
   * Handle WebSocket message (new telemetry data)
   */
  const handleTelemetryMessage = useCallback((data: TelemetryReading) => {
    setLiveMetrics(data);
    
    // Optionally add to historical data for real-time chart updates
    setHistoricalData(prev => {
      const updated = [...prev, data];
      // Keep only data within the current time range
      const cutoffTime = new Date();
      switch (timeRange) {
        case '6h':
          cutoffTime.setHours(cutoffTime.getHours() - 6);
          break;
        case '12h':
          cutoffTime.setHours(cutoffTime.getHours() - 12);
          break;
        case '24h':
          cutoffTime.setHours(cutoffTime.getHours() - 24);
          break;
      }
      return updated.filter(item => new Date(item.timestamp) >= cutoffTime);
    });
  }, [timeRange]);

  /**
   * Handle WebSocket status changes
   */
  const handleStatusChange = useCallback((status: ConnectionStatus) => {
    setWsConnected(status === ConnectionStatus.CONNECTED);
  }, []);

  /**
   * Handle WebSocket errors
   */
  const handleWebSocketError = useCallback((err: Error) => {
    console.error('WebSocket error:', err);
    // Don't show error to user for WebSocket issues - it will auto-reconnect
  }, []);

  /**
   * Initialize WebSocket connection on mount
   */
  useEffect(() => {
    telemetryWebSocket.connect(
      handleTelemetryMessage,
      handleStatusChange,
      handleWebSocketError
    );

    return () => {
      telemetryWebSocket.disconnect();
    };
  }, [handleTelemetryMessage, handleStatusChange, handleWebSocketError]);

  /**
   * Fetch historical data on mount and when time range changes
   */
  useEffect(() => {
    fetchHistoricalData();
  }, [fetchHistoricalData]);

  /**
   * Format live metric values
   */
  const formatMetricValue = (value: number | undefined, decimals = 2): string => {
    return value !== undefined ? value.toFixed(decimals) : '--';
  };

  /**
   * Get connection status indicator
   */
  const getConnectionIndicator = () => {
    if (wsConnected) {
      return (
        <div className="flex items-center text-green-600">
          <div className="w-2 h-2 bg-green-600 rounded-full mr-2 animate-pulse"></div>
          <span className="text-sm font-medium">Live</span>
        </div>
      );
    }
    return (
      <div className="flex items-center text-gray-400">
        <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
        <span className="text-sm font-medium">Connecting...</span>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-bold text-gray-900">
              Energy Optimization ROI Dashboard
            </h1>
            {getConnectionIndicator()}
          </div>
          <p className="text-gray-600">
            AI-powered generator optimization and cost savings analysis
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-600 hover:text-red-800"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Live Metrics Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Live Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Current Power Load */}
            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600">Current Power Load</h3>
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {formatMetricValue(liveMetrics?.power_load_kw)}
              </p>
              <p className="text-sm text-gray-500 mt-1">kW</p>
            </div>

            {/* Current Fuel Consumption */}
            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600">Fuel Consumption</h3>
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {formatMetricValue(liveMetrics?.fuel_consumption_lph)}
              </p>
              <p className="text-sm text-gray-500 mt-1">L/h</p>
            </div>

            {/* Generator Status */}
            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600">Generator Status</h3>
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {liveMetrics?.status || '--'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {liveMetrics?.timestamp 
                  ? `Updated ${new Date(liveMetrics.timestamp).toLocaleTimeString()}`
                  : 'Waiting for data...'}
              </p>
            </div>
          </div>
        </div>

        {/* Time Range Selector and Optimize Button */}
        <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Range
            </label>
            <div className="flex gap-2">
              {(['6h', '12h', '24h'] as TimeRange[]).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    timeRange === range
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>

          <div className="sm:mt-6">
            <button
              onClick={handleOptimize}
              disabled={isOptimizing || historicalData.length === 0}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                isOptimizing || historicalData.length === 0
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl'
              }`}
            >
              {isOptimizing ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing...
                </span>
              ) : (
                <span className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  Optimize Energy Usage
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Historical Charts Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Historical Data</h2>
          {isLoadingHistory ? (
            <div className="bg-white rounded-lg shadow p-12 border border-gray-200">
              <div className="flex items-center justify-center">
                <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="ml-3 text-gray-600">Loading historical data...</span>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Power Load Chart */}
              <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
                <PowerLoadChart data={historicalData} timeRange={timeRange} />
              </div>

              {/* Fuel Consumption Chart */}
              <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
                <FuelConsumptionChart data={historicalData} timeRange={timeRange} />
              </div>
            </div>
          )}
        </div>

        {/* ROI Card - Conditionally Rendered */}
        {optimization && (
          <div className="mb-8">
            <ROICard 
              optimization={optimization} 
              onDismiss={() => setOptimization(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
