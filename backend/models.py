"""
Data models for the Energy Optimization ROI Dashboard.

This module defines SQLModel and Pydantic models for:
- TelemetryReading: Time-series data from generator IoT simulation
- OptimizationResult: AI-generated optimization recommendations
- ShutdownWindow: Recommended generator shutdown period
- Savings: Projected cost savings from optimization
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel, field_validator


# SQLModel for database table
class TelemetryReading(SQLModel, table=True):
    """
    Represents a single telemetry reading from the generator.
    
    Stored in the time-series database with timestamp indexing for
    efficient historical queries.
    """
    __tablename__ = "telemetry"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True, description="UTC timestamp of the reading")
    power_load_kw: float = Field(ge=0, description="Power load in kilowatts")
    fuel_consumption_lph: float = Field(ge=0, description="Fuel consumption rate in liters per hour")
    status: str = Field(default="ON", description="Generator status (ON/OFF)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-14T10:30:00Z",
                "power_load_kw": 150.5,
                "fuel_consumption_lph": 45.2,
                "status": "ON"
            }
        }


# Pydantic models for API responses
class ShutdownWindow(BaseModel):
    """
    Represents the recommended time window for generator shutdown.
    """
    start: datetime
    end: datetime
    duration_hours: float
    
    @field_validator('duration_hours')
    @classmethod
    def validate_duration(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class Savings(BaseModel):
    """
    Represents projected cost savings from the optimization.
    """
    daily_savings_usd: float
    monthly_savings_usd: float
    fuel_saved_liters: float
    
    @field_validator('daily_savings_usd', 'monthly_savings_usd', 'fuel_saved_liters')
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Savings values must be non-negative")
        return v


class OptimizationResult(BaseModel):
    """
    Complete optimization recommendation including shutdown window,
    savings projections, and natural language recommendation.
    """
    shutdown_window: ShutdownWindow
    savings: Savings
    recommendation: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "shutdown_window": {
                    "start": "2025-11-14T02:00:00Z",
                    "end": "2025-11-14T06:00:00Z",
                    "duration_hours": 4.0
                },
                "savings": {
                    "daily_savings_usd": 120.50,
                    "monthly_savings_usd": 3615.00,
                    "fuel_saved_liters": 180.0
                },
                "recommendation": "Based on usage patterns, shutting down the generator between 2 AM and 6 AM could save approximately $120 per day with minimal operational impact."
            }
        }
