"""
IoT Simulator for generating realistic generator telemetry data.

This module simulates IoT sensor data from a remote generator, producing
realistic power load and fuel consumption readings with daily usage patterns.
"""

import os
import asyncio
import math
import random
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, select
from models import TelemetryReading
from database import get_session


# Configuration from environment variables
SIMULATION_INTERVAL_SECONDS = int(os.getenv("SIMULATION_INTERVAL_SECONDS", "2"))
MIN_POWER_LOAD_KW = float(os.getenv("MIN_POWER_LOAD_KW", "50"))
MAX_POWER_LOAD_KW = float(os.getenv("MAX_POWER_LOAD_KW", "300"))
FUEL_EFFICIENCY_FACTOR = float(os.getenv("FUEL_EFFICIENCY_FACTOR", "0.3"))


def generate_telemetry_reading(timestamp: Optional[datetime] = None) -> TelemetryReading:
    """
    Generate a single telemetry reading with realistic daily usage patterns.
    
    Uses a sine wave pattern to simulate daily cycles where power usage is:
    - Higher during daytime hours (peak around 2 PM)
    - Lower during nighttime hours (minimum around 3 AM)
    
    Args:
        timestamp: Optional timestamp for the reading. If None, uses current UTC time.
        
    Returns:
        TelemetryReading: Generated telemetry data with power load, fuel consumption,
                         status, and timestamp.
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Calculate hour of day for sine wave pattern (0-23)
    hour_of_day = timestamp.hour + timestamp.minute / 60.0
    
    # Create sine wave pattern with peak at 14:00 (2 PM) and trough at 03:00 (3 AM)
    # Shift the sine wave so that hour 14 is at the peak
    phase_shift = (hour_of_day - 14) * (2 * math.pi / 24)
    sine_value = math.sin(phase_shift)
    
    # Map sine wave (-1 to 1) to power load range
    # Invert sine so peak is at 2 PM (sine_value = 0 at phase_shift = 0)
    power_range = MAX_POWER_LOAD_KW - MIN_POWER_LOAD_KW
    base_power = MIN_POWER_LOAD_KW + (power_range / 2) * (1 - sine_value)
    
    # Add random noise (±10% of range)
    noise = random.uniform(-0.1, 0.1) * power_range
    power_load_kw = max(MIN_POWER_LOAD_KW, min(MAX_POWER_LOAD_KW, base_power + noise))
    
    # Calculate fuel consumption proportional to power load
    # Using the efficiency factor from configuration
    fuel_consumption_lph = power_load_kw * FUEL_EFFICIENCY_FACTOR
    
    # Generator status (always ON for simulation)
    status = "ON"
    
    return TelemetryReading(
        timestamp=timestamp,
        power_load_kw=round(power_load_kw, 2),
        fuel_consumption_lph=round(fuel_consumption_lph, 2),
        status=status
    )


async def seed_historical_data(hours: int = 24) -> int:
    """
    Seed the database with historical telemetry data.
    
    Generates synthetic data for the specified number of hours before the current time,
    with readings every 2 seconds to match the simulation interval.
    
    Args:
        hours: Number of hours of historical data to generate (default: 24)
        
    Returns:
        int: Number of records inserted into the database
    """
    print(f"Seeding {hours} hours of historical telemetry data...")
    
    current_time = datetime.utcnow()
    start_time = current_time - timedelta(hours=hours)
    
    # Generate readings every SIMULATION_INTERVAL_SECONDS
    readings: List[TelemetryReading] = []
    timestamp = start_time
    
    while timestamp <= current_time:
        reading = generate_telemetry_reading(timestamp)
        readings.append(reading)
        timestamp += timedelta(seconds=SIMULATION_INTERVAL_SECONDS)
    
    # Batch insert for performance
    with get_session() as session:
        # Check if data already exists to avoid duplicates
        existing_count = session.exec(select(TelemetryReading)).first()
        
        if existing_count is not None:
            print("Historical data already exists. Skipping seed.")
            return 0
        
        session.add_all(readings)
        session.commit()
    
    print(f"Successfully seeded {len(readings)} telemetry readings")
    return len(readings)


async def run_simulator_loop(callback: Optional[callable] = None) -> None:
    """
    Run the continuous IoT simulator loop.
    
    Generates new telemetry data every SIMULATION_INTERVAL_SECONDS and stores it
    in the database. Optionally calls a callback function with each new reading
    for real-time broadcasting (e.g., via WebSocket).
    
    Args:
        callback: Optional async function to call with each new reading.
                 Should accept a TelemetryReading parameter.
                 
    This function runs indefinitely until cancelled.
    """
    print(f"Starting IoT simulator (interval: {SIMULATION_INTERVAL_SECONDS}s)")
    
    while True:
        try:
            # Generate new reading
            reading = generate_telemetry_reading()
            
            # Store in database
            with get_session() as session:
                session.add(reading)
                session.commit()
                session.refresh(reading)
            
            # Call callback if provided (for WebSocket broadcasting)
            if callback is not None:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reading)
                else:
                    callback(reading)
            
            # Wait for next interval
            await asyncio.sleep(SIMULATION_INTERVAL_SECONDS)
            
        except Exception as e:
            print(f"Error in simulator loop: {e}")
            # Continue running even if there's an error
            await asyncio.sleep(SIMULATION_INTERVAL_SECONDS)


# Global task reference for managing the simulator
_simulator_task: Optional[asyncio.Task] = None


async def start_simulator(callback: Optional[callable] = None) -> None:
    """
    Start the IoT simulator as a background task.
    
    Args:
        callback: Optional async function to call with each new reading
    """
    global _simulator_task
    
    if _simulator_task is not None and not _simulator_task.done():
        print("Simulator is already running")
        return
    
    _simulator_task = asyncio.create_task(run_simulator_loop(callback))
    print("IoT simulator started as background task")


async def stop_simulator() -> None:
    """
    Stop the IoT simulator background task.
    """
    global _simulator_task
    
    if _simulator_task is not None and not _simulator_task.done():
        _simulator_task.cancel()
        try:
            await _simulator_task
        except asyncio.CancelledError:
            print("IoT simulator stopped")
        _simulator_task = None
    else:
        print("Simulator is not running")
