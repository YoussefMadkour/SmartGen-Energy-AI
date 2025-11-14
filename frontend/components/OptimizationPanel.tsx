import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface OptimizationResult {
  shutdown_window: {
    start: string;
    end: string;
    duration_hours: number;
  };
  savings: {
    daily_savings_usd: number;
    monthly_savings_usd: number;
    fuel_saved_liters: number;
  };
  recommendation: string;
}

export const OptimizationPanel: React.FC = () => {
  const [optimization, setOptimization] = useState<OptimizationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchOptimization = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/metrics/optimize', null, {
        params: { hours: 24 }
      });
      setOptimization(response.data);
    } catch (err: any) {
      console.error('Failed to fetch optimization:', err);
      setError(err.response?.data?.detail || 'Failed to fetch optimization recommendations');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchOptimization();
    // Set up periodic refresh (every hour)
    const interval = setInterval(fetchOptimization, 3600000);
    return () => clearInterval(interval);
  }, []);
  
  if (loading && !optimization) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-md">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-600">Analyzing generator performance...</span>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-md">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <strong>Error:</strong> {error}
        </div>
        <button 
          onClick={fetchOptimization}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }
  
  if (!optimization) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-md">
        <div className="text-gray-500">No optimization data available</div>
      </div>
    );
  }
  
  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-6 text-gray-800">AI Optimization Recommendations</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h3 className="text-lg font-semibold mb-3 text-blue-800">Recommended Shutdown Window</h3>
          <div className="space-y-2">
            <p className="text-sm text-gray-700">
              <span className="font-medium">Start:</span> {' '}
              {new Date(optimization.shutdown_window.start).toLocaleString()}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">End:</span> {' '}
              {new Date(optimization.shutdown_window.end).toLocaleString()}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Duration:</span> {' '}
              {optimization.shutdown_window.duration_hours} hours
            </p>
          </div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <h3 className="text-lg font-semibold mb-3 text-green-800">Projected Savings</h3>
          <div className="space-y-2">
            <p className="text-sm text-gray-700">
              <span className="font-medium">Daily:</span> {' '}
              <span className="text-green-600 font-bold">
                ${optimization.savings.daily_savings_usd.toFixed(2)}
              </span>
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Monthly:</span> {' '}
              <span className="text-green-600 font-bold">
                ${optimization.savings.monthly_savings_usd.toFixed(2)}
              </span>
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Fuel Saved:</span> {' '}
              <span className="text-green-600 font-bold">
                {optimization.savings.fuel_saved_liters.toFixed(2)} liters
              </span>
            </p>
          </div>
        </div>
      </div>
      
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-3 text-gray-800">AI Recommendation</h3>
        <p className="text-sm text-gray-700 leading-relaxed">
          {optimization.recommendation}
        </p>
      </div>
      
      <div className="mt-6 flex justify-between items-center">
        <button 
          onClick={fetchOptimization}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300 transition-colors"
        >
          {loading ? 'Analyzing...' : 'Refresh Analysis'}
        </button>
        
        <div className="text-xs text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>
    </div>
  );
};
