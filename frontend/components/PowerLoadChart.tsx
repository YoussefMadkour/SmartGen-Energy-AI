import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';
import { TelemetryReading } from '@/types';

interface PowerLoadChartProps {
  data: TelemetryReading[];
  timeRange?: string;
}

/**
 * Custom tooltip component for power load chart
 */
const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const timestamp = new Date(data.timestamp);
    
    return (
      <div className="bg-white p-3 border border-gray-300 rounded-lg shadow-lg">
        <p className="text-sm font-semibold text-gray-800">
          {timestamp.toLocaleString()}
        </p>
        <p className="text-sm text-blue-600 font-medium mt-1">
          Power Load: {data.power_load_kw.toFixed(2)} kW
        </p>
      </div>
    );
  }
  return null;
};

/**
 * Format timestamp for x-axis labels
 */
const formatXAxis = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
};

/**
 * PowerLoadChart component displays historical power load data
 * using a line chart with responsive dimensions and formatted tooltips
 */
export const PowerLoadChart: React.FC<PowerLoadChartProps> = ({ data, timeRange }) => {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-80 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">No power load data available</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-2">
        <h3 className="text-lg font-semibold text-gray-800">Power Load Over Time</h3>
        {timeRange && (
          <p className="text-sm text-gray-500">Time Range: {timeRange}</p>
        )}
      </div>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatXAxis}
            stroke="#666"
            style={{ fontSize: '12px' }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            stroke="#666"
            style={{ fontSize: '12px' }}
            label={{ 
              value: 'Power (kW)', 
              angle: -90, 
              position: 'insideLeft',
              style: { fontSize: '14px', fill: '#666' }
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="power_load_kw"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6, fill: '#3b82f6' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
