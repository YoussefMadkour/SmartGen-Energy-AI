"""
WebSocket Service for real-time telemetry streaming.

This module provides WebSocket functionality to push live generator telemetry
data to connected dashboard clients in real-time.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
from datetime import datetime
from models import TelemetryReading


class ConnectionManager:
    """
    Manages active WebSocket connections and handles broadcasting.
    
    Tracks all connected clients and provides methods to broadcast
    telemetry data to all active connections.
    """
    
    def __init__(self):
        """Initialize the connection manager with an empty connections list."""
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection and add it to active connections.
        
        Args:
            websocket: The WebSocket connection to accept and track
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from active connections.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all active WebSocket connections.
        
        Automatically removes connections that fail to receive the message
        (e.g., due to client disconnect).
        
        Args:
            message: Dictionary to send as JSON to all connected clients
        """
        # Create a copy of the list to avoid modification during iteration
        connections_to_remove = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                connections_to_remove.append(connection)
        
        # Remove failed connections
        for connection in connections_to_remove:
            self.disconnect(connection)
    
    async def broadcast_telemetry(self, reading: TelemetryReading) -> None:
        """
        Broadcast a telemetry reading to all connected clients.
        
        Formats the reading as a JSON message with type and data fields.
        
        Args:
            reading: TelemetryReading object to broadcast
        """
        message = {
            "type": "telemetry",
            "data": {
                "id": reading.id,
                "timestamp": reading.timestamp.isoformat() if isinstance(reading.timestamp, datetime) else reading.timestamp,
                "power_load_kw": reading.power_load_kw,
                "fuel_consumption_lph": reading.fuel_consumption_lph,
                "status": reading.status
            }
        }
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """
        Get the number of active WebSocket connections.
        
        Returns:
            int: Number of active connections
        """
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint handler for /ws/telemetry.
    
    Handles the complete lifecycle of a WebSocket connection:
    - Accept the connection
    - Keep the connection alive
    - Handle disconnection gracefully
    - Handle errors
    
    Args:
        websocket: The WebSocket connection from the client
    """
    await manager.connect(websocket)
    
    try:
        # Keep the connection alive and listen for messages
        # (In this implementation, we only push data, but we need to keep listening)
        while True:
            # Wait for any message from client (e.g., ping/pong)
            # This keeps the connection alive
            data = await websocket.receive_text()
            
            # Optional: Handle client messages if needed
            # For now, we just acknowledge receipt
            if data:
                try:
                    client_message = json.loads(data)
                    # Could handle client commands here (e.g., subscribe to specific metrics)
                    print(f"Received client message: {client_message}")
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {data}")
                    
    except WebSocketDisconnect:
        # Client disconnected normally
        manager.disconnect(websocket)
        print("Client disconnected normally")
    except Exception as e:
        # Handle any other errors
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.
    
    Returns:
        ConnectionManager: The global connection manager
    """
    return manager
