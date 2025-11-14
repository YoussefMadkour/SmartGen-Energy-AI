"""
FastAPI application for Energy Optimization ROI Dashboard.

This is the main entry point for the backend API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from database import init_database
from iot_simulator import seed_historical_data, start_simulator
from metrics_service import router as metrics_router


# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Startup:
        - Initialize database tables
        - Seed 24 hours of historical data
        - Start IoT simulator background task
        
    Shutdown:
        - Clean up resources
    """
    # Startup
    print("Starting Energy Optimization ROI Dashboard backend...")
    init_database()
    await seed_historical_data(hours=24)
    await start_simulator()
    
    yield
    
    # Shutdown
    print("Shutting down backend...")


# Create FastAPI application
app = FastAPI(
    title="Energy Optimization ROI Dashboard API",
    description="Backend API for generator telemetry monitoring and AI-powered optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "status": "online",
        "service": "Energy Optimization ROI Dashboard API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Register service routers
app.include_router(metrics_router)
