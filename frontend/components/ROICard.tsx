import React from 'react';
import { OptimizationResult } from '@/types';

interface ROICardProps {
  optimization: OptimizationResult;
  onDismiss?: () => void;
}

/**
 * ROI Card Component
 * Displays optimization recommendations with shutdown window, savings projections, and AI recommendation
 */
export const ROICard: React.FC<ROICardProps> = ({ optimization, onDismiss }) => {
  // Format date and time for display
  const formatDateTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  // Format time only for display
  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const { shutdown_window, savings, recommendation } = optimization;

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Optimization Recommendation</h2>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-white hover:text-gray-200 transition-colors"
              aria-label="Dismiss"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="p-6">
        {/* Shutdown Window Section */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
            Recommended Shutdown Window
          </h3>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex-1">
                <p className="text-xs text-gray-600 mb-1">Start Time</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatDateTime(shutdown_window.start)}
                </p>
              </div>
              <div className="px-4">
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
              <div className="flex-1 text-right">
                <p className="text-xs text-gray-600 mb-1">End Time</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatDateTime(shutdown_window.end)}
                </p>
              </div>
            </div>
            
            {/* Duration Badge */}
            <div className="flex justify-center">
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-blue-600 text-white">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {shutdown_window.duration_hours} {shutdown_window.duration_hours === 1 ? 'hour' : 'hours'}
              </span>
            </div>
          </div>
        </div>

        {/* Savings Section */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
            Projected Savings
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Daily Savings - Prominent Display */}
            <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm font-medium text-gray-700">Daily Savings</span>
              </div>
              <p className="text-3xl font-bold text-green-600">
                ${savings.daily_savings_usd.toFixed(2)}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {savings.fuel_saved_liters.toFixed(1)} liters saved
              </p>
            </div>

            {/* Monthly Projection */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-sm font-medium text-gray-700">Monthly Projection</span>
              </div>
              <p className="text-3xl font-bold text-green-600">
                ${savings.monthly_savings_usd.toFixed(2)}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                Based on 30-day period
              </p>
            </div>
          </div>
        </div>

        {/* AI Recommendation Section */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">AI Recommendation</h3>
              <p className="text-sm text-gray-700 leading-relaxed">
                {recommendation}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
