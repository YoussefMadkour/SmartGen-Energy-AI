"""
Metrics Service for Energy Optimization ROI Dashboard.

This module provides REST endpoints for:
- Storing telemetry data (internal use by IoT simulator)
- Retrieving historical telemetry data with time-range filtering
- Fetching latest telemetry reading
- AI-powered optimization recommendations

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.5
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel
import os

from database import get_db_session
from models import TelemetryReading, OptimizationResult
from agent_service import run_optimization_analysis


# Create router for metrics endpoints
router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


# Request/Response models
class TelemetryBatchRequest(BaseModel):
    """Request model for batch telemetry insertion."""
    readings: List[TelemetryReading]


class HistoricalDataResponse(BaseModel):
    """Response model for historical data queries."""
    count: int
    start: datetime
    end: datetime
    data: List[TelemetryReading]


class OptimizationRequest(BaseModel):
    """Request model for optimization analysis."""
    hours: int = 24  # Default to 24 hours of data


# Database query functions
def store_telemetry_reading(session: Session, reading: TelemetryReading) -> TelemetryReading:
    """
    Store a single telemetry reading in the database.
    
    Args:
        session: Database session
        reading: TelemetryReading object to store
        
    Returns:
        TelemetryReading: The stored reading with assigned ID
    """
    session.add(reading)
    session.commit()
    session.refresh(reading)
    return reading


def store_telemetry_batch(session: Session, readings: List[TelemetryReading]) -> int:
    """
    Store multiple telemetry readings in a single transaction for performance.
    
    This function implements batch insert optimization to reduce database
    round-trips when storing multiple readings.
    
    Args:
        session: Database session
        readings: List of TelemetryReading objects to store
        
    Returns:
        int: Number of readings stored
    """
    session.add_all(readings)
    session.commit()
    return len(readings)


def get_historical_telemetry(
    session: Session,
    start: datetime,
    end: datetime
) -> List[TelemetryReading]:
    """
    Query historical telemetry data within a time range.
    
    Uses indexed timestamp column for efficient queries.
    
    Args:
        session: Database session
        start: Start of time range (inclusive)
        end: End of time range (inclusive)
        
    Returns:
        List[TelemetryReading]: Telemetry readings ordered by timestamp
    """
    statement = (
        select(TelemetryReading)
        .where(TelemetryReading.timestamp >= start)
        .where(TelemetryReading.timestamp <= end)
        .order_by(TelemetryReading.timestamp)
    )
    results = session.exec(statement).all()
    return list(results)


def get_latest_telemetry(session: Session) -> Optional[TelemetryReading]:
    """
    Retrieve the most recent telemetry reading.
    
    Args:
        session: Database session
        
    Returns:
        Optional[TelemetryReading]: Latest reading or None if no data exists
    """
    statement = (
        select(TelemetryReading)
        .order_by(TelemetryReading.timestamp.desc())
        .limit(1)
    )
    result = session.exec(statement).first()
    return result


# REST Endpoints
@router.post("/", status_code=201, response_model=TelemetryReading)
async def store_telemetry(
    reading: TelemetryReading,
    session: Session = Depends(get_db_session)
) -> TelemetryReading:
    """
    Store a single telemetry reading (internal use by IoT simulator).
    
    This endpoint is used by the IoT simulator to persist generated
    telemetry data.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    try:
        stored_reading = store_telemetry_reading(session, reading)
        return stored_reading
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store telemetry reading: {str(e)}"
        )


@router.post("/batch", status_code=201)
async def store_telemetry_batch_endpoint(
    batch: TelemetryBatchRequest,
    session: Session = Depends(get_db_session)
) -> dict:
    """
    Store multiple telemetry readings in a batch (optimized for performance).
    
    This endpoint implements batch insert optimization to reduce database
    overhead when storing multiple readings at once.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    try:
        count = store_telemetry_batch(session, batch.readings)
        return {
            "status": "success",
            "count": count,
            "message": f"Successfully stored {count} telemetry readings"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store telemetry batch: {str(e)}"
        )


@router.get("/history", response_model=HistoricalDataResponse)
async def get_historical_data(
    start: Optional[datetime] = Query(
        None,
        description="Start of time range (ISO 8601 format). Defaults to 24 hours ago."
    ),
    end: Optional[datetime] = Query(
        None,
        description="End of time range (ISO 8601 format). Defaults to now."
    ),
    session: Session = Depends(get_db_session)
) -> HistoricalDataResponse:
    """
    Retrieve historical telemetry data within a specified time range.
    
    If no time range is specified, returns the last 24 hours of data.
    
    Query Parameters:
        - start: Start timestamp (ISO 8601 format)
        - end: End timestamp (ISO 8601 format)
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.5
    """
    # Default to last 24 hours if not specified
    if end is None:
        end = datetime.utcnow()
    if start is None:
        start = end - timedelta(hours=24)
    
    # Validate time range
    if start > end:
        raise HTTPException(
            status_code=400,
            detail="Start time must be before end time"
        )
    
    try:
        data = get_historical_telemetry(session, start, end)
        return HistoricalDataResponse(
            count=len(data),
            start=start,
            end=end,
            data=data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve historical data: {str(e)}"
        )


@router.get("/latest", response_model=TelemetryReading)
async def get_latest_reading(
    session: Session = Depends(get_db_session)
) -> TelemetryReading:
    """
    Retrieve the most recent telemetry reading.
    
    Returns the latest reading from the database, useful for displaying
    current generator status.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    try:
        latest = get_latest_telemetry(session)
        if latest is None:
            raise HTTPException(
                status_code=404,
                detail="No telemetry data available"
            )
        return latest
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve latest reading: {str(e)}"
        )


@router.post("/optimize", response_model=OptimizationResult)
async def optimize_generator_performance(
    hours: int = Query(24, description="Hours of historical data to analyze"),
    session: Session = Depends(get_db_session)
) -> OptimizationResult:
    """
    Analyze historical telemetry data and generate optimization recommendations.
    
    This endpoint uses the AI agent to analyze usage patterns and recommend
    optimal shutdown windows to save fuel costs.
    
    Args:
        hours: Number of hours of historical data to analyze
        session: Database session
        
    Returns:
        OptimizationResult: Complete optimization recommendation
        
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    """
    try:
        # Get historical data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        telemetry_data = get_historical_telemetry(session, start_time, end_time)
        
        if not telemetry_data:
            raise HTTPException(
                status_code=404,
                detail="No telemetry data available for optimization"
            )
        
        # Get fuel price from environment
        fuel_price = float(os.getenv("DIESEL_PRICE_PER_LITER", "1.50"))
        
        # Run agent analysis
        optimization_result = await run_optimization_analysis(telemetry_data, fuel_price)
        
        if optimization_result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate optimization recommendations"
            )
        
        return optimization_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize generator performance: {str(e)}"
        )
