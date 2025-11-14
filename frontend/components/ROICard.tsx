import React, { useState } from 'react';
import axios from 'axios';

interface ROIData {
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
  analysis_period_hours: number;
  last_updated: string;
}

interface ROICardProps {
  analysisHours?: number;
}

export const ROICard: React.FC<ROICardProps> = ({ analysisHours = 24 }) => {
  const [roiData, setRoiData] = useState<ROIData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchROIData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`/api/insights/roi?hours=${analysisHours}`);
      setRoiData(response.data);
    } catch (err: any) {
      console.error('Failed to fetch ROI data:', err);
      setError(err.response?.data?.detail || 'Failed to fetch optimization insights');
    } finally {
      setLoading(false);
    }
  };
  
  React.useEffect(() => {
    fetchROIData();
    // Set up periodic refresh (every 30 minutes)
    const interval = setInterval(fetchROIData, 1800000);
    return () => clearInterval(interval);
  }, [analysisHours]);
  
  if (loading && !roiData) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-md">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-600">Analyzing optimization opportunities...</span>
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
          onClick={fetchROIData}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }
  
  if (!roiData) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-md">
        <div className="text-gray-500">No ROI data available</div>
      </div>
    );
  }
  
  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-800">Optimization Insights</h2>
        <div className="text-sm text-gray-500">
          Analysis Period: {roiData.analysis_period_hours} hours | 
          Last Updated: {new Date(roiData.last_updated).toLocaleString()}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h3 className="text-lg font-semibold mb-3 text-blue-800">Recommended Shutdown Window</h3>
          <div className="space-y-2">
            <p className="text-sm text-gray-700">
              <span className="font-medium">Start:</span> {' '}
              {new Date(roiData.shutdown_window.start).toLocaleString()}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">End:</span> {' '}
              {new Date(roiData.shutdown_window.end).toLocaleString()}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Duration:</span> {' '}
              {roiData.shutdown_window.duration_hours} hours
            </p>
          </div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <h3 className="text-lg font-semibold mb-3 text-green-800">Projected Savings</h3>
          <div className="space-y-2">
            <p className="text-sm text-gray-700">
              <span className="font-medium">Daily:</span> {' '}
              <span className="text-green-600 font-bold">
                ${roiData.savings.daily_savings_usd.toFixed(2)}
              </span>
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Monthly:</span> {' '}
              <span className="text-green-600 font-bold">
                ${roiData.savings.monthly_savings_usd.toFixed(2)}
              </span>
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Fuel Saved:</span> {' '}
              <span className="text-green-600 font-bold">
                {roiData.savings.fuel_saved_liters.toFixed(2)} liters
              </span>
            </p>
          </div>
        </div>
      </div>
      
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-3 text-gray-800">AI Recommendation</h3>
        <p className="text-sm text-gray-700 leading-relaxed">
          {roiData.recommendation}
        </p>
      </div>
      
      <div className="mt-6 flex justify-between items-center">
        <button 
          onClick={fetchROIData}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300 transition-colors"
        >
          {loading ? 'Analyzing...' : 'Refresh Analysis'}
        </button>
        
        <div className="text-xs text-gray-500">
          Analysis based on last {roiData.analysis_period_hours} hours of data
        </div>
      </div>
    </div>
  );
};
