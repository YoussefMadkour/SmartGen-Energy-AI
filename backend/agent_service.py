"""
AI Agent Service for Energy Optimization.

This module implements a LangGraph agent that analyzes telemetry data
and generates optimization recommendations for generator operations.
"""

import os
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool

from database import get_session
from models import TelemetryReading, OptimizationResult, ShutdownWindow, Savings

# Initialize LLM
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4"),
    temperature=0.1
)

# Define agent state
class EnergyOptimizationState(TypedDict):
    telemetry_data: List[TelemetryReading]
    analysis_results: Dict[str, Any]
    optimization_result: Optional[OptimizationResult]
    messages: List[Any]
    fuel_price: float

# Define tools for the agent
@tool
def analyze_usage_patterns(telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze power usage patterns from telemetry data.
    
    Args:
        telemetry_data: List of telemetry readings with timestamps and power loads
        
    Returns:
        Dictionary containing usage pattern analysis
    """
    if not telemetry_data:
        return {"error": "No telemetry data provided"}
    
    # Extract power loads and timestamps
    power_loads = [reading["power_load_kw"] for reading in telemetry_data]
    timestamps = [reading["timestamp"] for reading in telemetry_data]
    
    # Calculate basic statistics
    avg_power = statistics.mean(power_loads)
    min_power = min(power_loads)
    max_power = max(power_loads)
    
    # Group by hour to find patterns
    hourly_usage = {}
    for reading in telemetry_data:
        hour = datetime.fromisoformat(reading["timestamp"].replace('Z', '+00:00')).hour
        if hour not in hourly_usage:
            hourly_usage[hour] = []
        hourly_usage[hour].append(reading["power_load_kw"])
    
    # Calculate average usage by hour
    hourly_avg = {hour: statistics.mean(loads) for hour, loads in hourly_usage.items()}
    
    # Find lowest usage hours (potential shutdown windows)
    sorted_hours = sorted(hourly_avg.items(), key=lambda x: x[1])
    lowest_usage_hours = [hour for hour, _ in sorted_hours[:4]]  # Top 4 lowest hours
    
    return {
        "avg_power": avg_power,
        "min_power": min_power,
        "max_power": max_power,
        "hourly_usage": hourly_avg,
        "lowest_usage_hours": lowest_usage_hours
    }

@tool
def calculate_optimal_shutdown(usage_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate optimal shutdown windows based on usage patterns.
    
    Args:
        usage_analysis: Results from usage pattern analysis
        
    Returns:
        Dictionary containing shutdown window recommendations
    """
    if "error" in usage_analysis:
        return {"error": usage_analysis["error"]}
    
    lowest_hours = usage_analysis["lowest_usage_hours"]
    
    # Find consecutive hours for optimal shutdown window
    best_window = []
    current_window = []
    
    for i in range(24):
        hour = (lowest_hours[0] + i) % 24
        if hour in lowest_hours:
            current_window.append(hour)
        else:
            if len(current_window) > len(best_window):
                best_window = current_window
            current_window = []
    
    # Check if the last window wraps around midnight
    if len(current_window) > len(best_window):
        best_window = current_window
    
    # Calculate start and end times
    if best_window:
        start_hour = min(best_window)
        end_hour = (max(best_window) + 1) % 24
        duration = len(best_window)
        
        # Create datetime objects for today
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_time = today + timedelta(hours=start_hour)
        
        if end_hour == 0:
            end_time = today + timedelta(days=1)
        else:
            end_time = today + timedelta(hours=end_hour)
        
        return {
            "start_time": start_time,
            "end_time": end_time,
            "duration_hours": duration,
            "recommended_hours": best_window
        }
    else:
        return {"error": "Could not determine optimal shutdown window"}

@tool
def calculate_savings(shutdown_window: Dict[str, Any], fuel_price: float, avg_fuel_consumption: float) -> Dict[str, Any]:
    """
    Calculate projected savings from shutdown recommendations.
    
    Args:
        shutdown_window: Recommended shutdown window data
        fuel_price: Price of fuel per liter
        avg_fuel_consumption: Average fuel consumption per hour
        
    Returns:
        Dictionary containing savings calculations
    """
    if "error" in shutdown_window:
        return {"error": shutdown_window["error"]}
    
    duration_hours = shutdown_window["duration_hours"]
    
    # Calculate fuel saved per day
    fuel_saved_per_day = avg_fuel_consumption * duration_hours
    
    # Calculate cost savings
    daily_savings = fuel_saved_per_day * fuel_price
    monthly_savings = daily_savings * 30  # Approximate month
    
    return {
        "daily_savings_usd": daily_savings,
        "monthly_savings_usd": monthly_savings,
        "fuel_saved_liters": fuel_saved_per_day
    }

# Define agent nodes
def analyze_data(state: EnergyOptimizationState):
    """Analyze telemetry data to identify patterns."""
    # Convert telemetry data to dict format for tools
    telemetry_dicts = [
        {
            "timestamp": reading.timestamp.isoformat(),
            "power_load_kw": reading.power_load_kw,
            "fuel_consumption_lph": reading.fuel_consumption_lph,
            "status": reading.status
        }
        for reading in state["telemetry_data"]
    ]
    
    # Use the analyze_usage_patterns tool
    analysis = analyze_usage_patterns(telemetry_dicts)
    
    return {
        **state,
        "analysis_results": analysis
    }

def generate_recommendations(state: EnergyOptimizationState):
    """Generate optimization recommendations based on analysis."""
    analysis = state["analysis_results"]
    
    if "error" in analysis:
        return {
            **state,
            "optimization_result": None
        }
    
    # Calculate optimal shutdown window
    shutdown_window = calculate_optimal_shutdown(analysis)
    
    if "error" in shutdown_window:
        return {
            **state,
            "optimization_result": None
        }
    
    # Calculate average fuel consumption
    avg_fuel_consumption = statistics.mean([
        reading.fuel_consumption_lph for reading in state["telemetry_data"]
    ])
    
    # Calculate savings
    savings_data = calculate_savings(
        shutdown_window, 
        state["fuel_price"], 
        avg_fuel_consumption
    )
    
    # Generate natural language recommendation
    recommendation_prompt = f"""
    Based on the generator usage analysis:
    - Average power consumption: {analysis['avg_power']:.2f} kW
    - Lowest usage hours: {analysis['lowest_usage_hours']}
    - Recommended shutdown window: {shutdown_window['start_time'].strftime('%H:%M')} to {shutdown_window['end_time'].strftime('%H:%M')} ({shutdown_window['duration_hours']} hours)
    - Daily savings: ${savings_data['daily_savings_usd']:.2f}
    - Monthly savings: ${savings_data['monthly_savings_usd']:.2f}
    
    Provide a concise recommendation for the operator explaining the benefits of this shutdown window.
    """
    
    messages = [
        SystemMessage(content="You are an expert energy optimization advisor for industrial generators. Provide clear, actionable recommendations."),
        HumanMessage(content=recommendation_prompt)
    ]
    
    response = llm.invoke(messages)
    
    # Create optimization result
    optimization_result = OptimizationResult(
        shutdown_window=ShutdownWindow(
            start=shutdown_window["start_time"],
            end=shutdown_window["end_time"],
            duration_hours=shutdown_window["duration_hours"]
        ),
        savings=Savings(
            daily_savings_usd=savings_data["daily_savings_usd"],
            monthly_savings_usd=savings_data["monthly_savings_usd"],
            fuel_saved_liters=savings_data["fuel_saved_liters"]
        ),
        recommendation=response.content
    )
    
    return {
        **state,
        "optimization_result": optimization_result
    }

# Build the agent graph
def create_energy_optimization_agent():
    """Create and compile the energy optimization agent."""
    workflow = StateGraph(EnergyOptimizationState)
    
    # Add nodes
    workflow.add_node("analyze_data", analyze_data)
    workflow.add_node("generate_recommendations", generate_recommendations)
    
    # Add edges
    workflow.add_edge(START, "analyze_data")
    workflow.add_edge("analyze_data", "generate_recommendations")
    workflow.add_edge("generate_recommendations", END)
    
    return workflow.compile()

# Initialize the agent
energy_agent = create_energy_optimization_agent()

async def run_optimization_analysis(telemetry_data: List[TelemetryReading], fuel_price: float = 1.50) -> Optional[OptimizationResult]:
    """
    Run the energy optimization analysis on telemetry data.
    
    Args:
        telemetry_data: List of telemetry readings to analyze
        fuel_price: Price of fuel per liter (default from environment)
        
    Returns:
        OptimizationResult: Complete optimization recommendation or None if analysis fails
    """
    if not telemetry_data:
        return None
    
    try:
        agent_input = {
            "telemetry_data": telemetry_data,
            "fuel_price": fuel_price,
            "messages": [SystemMessage(content="Analyze the generator telemetry data and provide optimization recommendations.")]
        }
        
        result = await energy_agent.ainvoke(agent_input)
        return result.get("optimization_result")
    except Exception as e:
        print(f"Error running optimization analysis: {e}")
        return None
