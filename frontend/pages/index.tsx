import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { OptimizationPanel } from '../components/OptimizationPanel';

interface TelemetryReading {
  id: number;
  timestamp: string;
  power_load_kw: number;
  fuel_consumption_lph: number;
  status: string;
}

const Dashboard: React.FC = () => {
  const [telemetryData, setTelemetryData] = useState<TelemetryReading[]>([]);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('Disconnected');

  useEffect(() => {
    // Fetch initial historical data
    const fetchHistoricalData = async () => {
      try {
        const response = await axios.get('/api/metrics/history?hours=24');
        setTelemetryData(response.data.data);
      } catch (error) {
        console.error('Error fetching historical data:', error);
      }
    };

    fetchHistoricalData();

    // Set up WebSocket connection for real-time updates
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/ws/telemetry`);
    
    ws.onopen = () => {
      setConnectionStatus('Connected');
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'telemetry') {
        setTelemetryData(prevData => [...prevData.slice(-100), message.data]); // Keep last 100 readings
      }
    };
    
    ws.onclose = () => {
      setConnectionStatus('Disconnected');
      console.log('WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      setConnectionStatus('Error');
      console.error('WebSocket error:', error);
    };
    
    setWsConnection(ws);
    
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Energy Optimization Dashboard</h1>
          <div className="flex items-center mt-2">
            <div className={`h-3 w-3 rounded-full mr-2 ${
              connectionStatus === 'Connected' ? 'bg-green-500' : 
              connectionStatus === 'Error' ? 'bg-red-500' : 'bg-gray-500'
            }`}></div>
            <span className="text-sm text-gray-600">
              {connectionStatus === 'Connected' ? 'Live' : 
               connectionStatus === 'Error' ? 'Connection Error' : 'Offline'}
            </span>
          </div>
        </header>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Telemetry Chart */}
          <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">Generator Telemetry</h2>
            <div className="h-96 flex items-center justify-center bg-gray-50 rounded">
              <p className="text-gray-500">Telemetry chart component would go here</p>
              <p className="text-sm text-gray-400 mt-2">Integration with Recharts for visualization</p>
            </div>
          </div>
          
          {/* Current Status */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">Current Status</h2>
            {telemetryData.length > 0 ? (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Power Load:</span>
                  <span className="font-medium">{telemetryData[telemetryData.length - 1].power_load_kw} kW</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Fuel Consumption:</span>
                  <span className="font-medium">{telemetryData[telemetryData.length - 1].fuel_consumption_lph} L/h</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className={`font-medium ${
                    telemetryData[telemetryData.length - 1].status === 'ON' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {telemetryData[telemetryData.length - 1].status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Update:</span>
                  <span className="font-medium text-sm">
                    {new Date(telemetryData[telemetryData.length - 1].timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-gray-500">No telemetry data available</div>
            )}
          </div>
        </div>
        
        {/* AI Optimization Panel */}
        <div className="mt-6">
          <OptimizationPanel />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
