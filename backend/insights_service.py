"""
Insights Service for Energy Optimization ROI Dashboard.

This module provides REST endpoints for AI-powered insights and optimization
recommendations based on generator telemetry data analysis.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel, Field, validator
import os

from database import get_db_session
from models import TelemetryReading, OptimizationResult, ShutdownWindow, Savings
from agent_service import run_optimization_analysis


# Create router for insights endpoints
router = APIRouter(prefix="/api/insights", tags=["Insights"])


# Request/Response models
class OptimizationRequest(BaseModel):
    """Request model for optimization analysis."""
    analysis_hours: int = Field(24, description="Hours of historical data to analyze")
    min_shutdown_hours: int = Field(2, description="Minimum shutdown duration in hours")
    max_shutdown_hours: int = Field(8, description="Maximum shutdown duration in hours")
    
    @validator('analysis_hours')
    def validate_analysis_hours(cls, v):
        if v < 1:
            raise ValueError('analysis_hours must be at least 1')
        return v
    
    @validator('min_shutdown_hours')
    def validate_min_shutdown_hours(cls, v):
        if v < 1:
            raise ValueError('min_shutdown_hours must be at least 1')
        return v
    
    @validator('max_shutdown_hours')
    def validate_max_shutdown_hours(cls, v):
        if v < 1:
            raise ValueError('max_shutdown_hours must be at least 1')
        return v


class ROICard(BaseModel):
    """ROI card data for dashboard display."""
    shutdown_window: ShutdownWindow
    savings: Savings
    recommendation: str
    analysis_period_hours: int
    last_updated: datetime


# Database query functions
def get_usage_profile(
    session: Session,
    hours: int
) -> List[TelemetryReading]:
    """
    Retrieve historical power load data for usage profile analysis.
    
    Args:
        session: Database session
        hours: Number of hours of historical data to retrieve
        
    Returns:
        List[TelemetryReading]: Historical telemetry data
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    statement = (
        select(TelemetryReading)
        .where(TelemetryReading.timestamp >= start_time)
        .where(TelemetryReading.timestamp <= end_time)
        .order_by(TelemetryReading.timestamp)
    )
    results = session.exec(statement).all()
    return list(results)


def compute_shutdown_window(
    usage_data: List[TelemetryReading],
    min_hours: int,
    max_hours: int
) -> dict:
    """
    Compute optimal shutdown window using sliding window algorithm.
    
    Args:
        usage_data: Historical telemetry data
        min_hours: Minimum shutdown duration in hours
        max_hours: Maximum shutdown duration in hours
        
    Returns:
        dict: Shutdown window calculation results
    """
    if not usage_data:
        return {"error": "No usage data provided"}
    
    # Group by hour to find patterns
    hourly_usage = {}
    for reading in usage_data:
        hour = reading.timestamp.hour
        if hour not in hourly_usage:
            hourly_usage[hour] = []
        hourly_usage[hour].append(reading.power_load_kw)
    
    # Calculate average usage by hour
    hourly_avg = {hour: sum(loads) / len(loads) for hour, loads in hourly_usage.items()}
    
    # Find consecutive hours with minimum usage
    sorted_hours = sorted(hourly_avg.items(), key=lambda x: x[1])
    lowest_hours = [hour for hour, _ in sorted_hours[:6]]  # Top 6 lowest hours
    
    # Find best consecutive window within constraints
    best_window = []
    best_start = None
    
    for start_hour in range(24):
        window = []
        current_hour = start_hour
        
        # Check consecutive hours
        for i in range(max_hours):
            hour = (current_hour + i) % 24
            if hour in lowest_hours:
                window.append(hour)
                current_hour = (hour + 1) % 24
            else:
                break
        
        # Check if window meets minimum duration
        if len(window) >= min_hours and len(window) <= max_hours:
            if len(window) > len(best_window):
                best_window = window
                best_start = start_hour
    
    if not best_window:
        return {"error": "Could not find suitable shutdown window"}
    
    # Calculate start and end times
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = today + timedelta(hours=best_start)
    end_hour = (best_start + len(best_window)) % 24
    
    if end_hour == 0:
        end_time = today + timedelta(days=1)
    else:
        end_time = today + timedelta(hours=end_hour)
    
    return {
        "start_time": start_time,
        "end_time": end_time,
        "duration_hours": len(best_window),
        "recommended_hours": best_window
    }


def estimate_savings(
    shutdown_window: dict,
    usage_data: List[TelemetryReading]
) -> dict:
    """
    Estimate fuel savings based on shutdown window and fuel consumption.
    
    Args:
        shutdown_window: Calculated shutdown window data
        usage_data: Historical telemetry data
        
    Returns:
        dict: Savings estimation results
    """
    if "error" in shutdown_window:
        return {"error": shutdown_window["error"]}
    
    # Calculate average fuel consumption
    avg_fuel_consumption = sum(reading.fuel_consumption_lph for reading in usage_data) / len(usage_data)
    
    # Get fuel price from environment
    fuel_price = float(os.getenv("DIESEL_PRICE_PER_LITER", "1.50"))
    
    # Calculate savings
    duration_hours = shutdown_window["duration_hours"]
    fuel_saved_per_day = avg_fuel_consumption * duration_hours
    daily_savings = fuel_saved_per_day * fuel_price
    monthly_savings = daily_savings * 30  # Approximate month
    
    return {
        "daily_savings_usd": daily_savings,
        "monthly_savings_usd": monthly_savings,
        "fuel_saved_liters": fuel_saved_per_day
    }


# REST Endpoints
@router.post("/optimize", response_model=OptimizationResult)
async def optimize_generator_performance(
    request: OptimizationRequest,
    session: Session = Depends(get_db_session)
) -> OptimizationResult:
    """
    Analyze historical telemetry data and generate optimization recommendations.
    
    This endpoint implements the Insights Service optimization functionality
    with deterministic tools for usage profile analysis, shutdown window
    calculation, and savings estimation.
    
    Args:
        request: Optimization request with analysis parameters
        session: Database session
        
    Returns:
        OptimizationResult: Complete optimization recommendation
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    try:
        # Get historical data using deterministic tool
        usage_data = get_usage_profile(session, request.analysis_hours)
        
        if not usage_data:
            raise HTTPException(
                status_code=404,
                detail="No telemetry data available for optimization"
            )
        
        # Compute optimal shutdown window using deterministic tool
        shutdown_window = compute_shutdown_window(
            usage_data, 
            request.min_shutdown_hours, 
            request.max_shutdown_hours
        )
        
        if "error" in shutdown_window:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to compute shutdown window: {shutdown_window['error']}"
            )
        
        # Estimate savings using deterministic tool
        savings = estimate_savings(shutdown_window, usage_data)
        
        if "error" in savings:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to estimate savings: {savings['error']}"
            )
        
        # Generate natural language recommendation using LangChain agent
        optimization_result = await run_optimization_analysis(
            usage_data, 
            float(os.getenv("DIESEL_PRICE_PER_LITER", "1.50"))
        )
        
        if not optimization_result:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate optimization recommendations"
            )
        
        # Return the optimization result directly (already has correct structure)
        return optimization_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize generator performance: {str(e)}"
        )


@router.get("/roi", response_model=ROICard)
async def get_roi_card(
    hours: int = Query(24, description="Hours of historical data to analyze"),
    session: Session = Depends(get_db_session)
) -> ROICard:
    """
    Generate ROI card with optimization recommendations for dashboard display.
    
    This endpoint provides formatted optimization data for the dashboard
    ROI card component.
    
    Args:
        hours: Number of hours of historical data to analyze
        session: Database session
        
    Returns:
        ROICard: Formatted ROI card data
        
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """
    try:
        # Get historical data
        usage_data = get_usage_profile(session, hours)
        
        if not usage_data:
            raise HTTPException(
                status_code=404,
                detail="No telemetry data available for optimization"
            )
        
        # Generate optimization
        optimization_result = await run_optimization_analysis(
            usage_data, 
            float(os.getenv("DIESEL_PRICE_PER_LITER", "1.50"))
        )
        
        if not optimization_result:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate optimization recommendations"
            )
        
        return ROICard(
            shutdown_window=optimization_result.shutdown_window,
            savings=optimization_result.savings,
            recommendation=optimization_result.recommendation,
            analysis_period_hours=hours,
            last_updated=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate ROI card: {str(e)}"
        )
