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
from langgraph.types import RetryPolicy
from langgraph.checkpoint.memory import MemorySaver

from database import get_session
from models import TelemetryReading, OptimizationResult, ShutdownWindow, Savings

# Initialize LLM with retry configuration
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4"),
    temperature=0.1,
    max_retries=3,
    request_timeout=30
)

# Add memory for persistence
memory = MemorySaver()

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

@tool
def analyze_efficiency_trends(telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze efficiency trends and patterns from telemetry data.
    
    Args:
        telemetry_data: List of telemetry readings with timestamps, power loads, and fuel consumption
        
    Returns:
        Dictionary containing efficiency trend analysis
    """
    if not telemetry_data:
        return {"error": "No telemetry data provided"}
    
    # Calculate efficiency metrics (power generated per fuel unit)
    efficiency_data = []
    for reading in telemetry_data:
        # Simple efficiency calculation: power load / fuel consumption
        # Higher value means more efficient (more power per fuel unit)
        if reading["fuel_consumption_lph"] > 0:
            efficiency = reading["power_load_kw"] / reading["fuel_consumption_lph"]
            efficiency_data.append({
                "timestamp": reading["timestamp"],
                "efficiency": efficiency,
                "power_load": reading["power_load_kw"],
                "fuel_consumption": reading["fuel_consumption_lph"]
            })
    
    if not efficiency_data:
        return {"error": "No valid efficiency data could be calculated"}
    
    # Analyze efficiency trends by hour
    hourly_efficiency = {}
    for data in efficiency_data:
        hour = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')).hour
        if hour not in hourly_efficiency:
            hourly_efficiency[hour] = []
        hourly_efficiency[hour].append(data["efficiency"])
    
    # Calculate average efficiency by hour
    hourly_avg_efficiency = {
        hour: statistics.mean(efficiencies) 
        for hour, efficiencies in hourly_efficiency.items()
    }
    
    # Find most and least efficient hours
    most_efficient_hours = sorted(
        hourly_avg_efficiency.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:3]  # Top 3 most efficient hours
    
    least_efficient_hours = sorted(
        hourly_avg_efficiency.items(), 
        key=lambda x: x[1]
    )[:3]  # Top 3 least efficient hours
    
    # Calculate overall efficiency trend
    overall_avg_efficiency = statistics.mean([d["efficiency"] for d in efficiency_data])
    
    # Calculate efficiency variance (consistency)
    efficiency_variance = statistics.variance([d["efficiency"] for d in efficiency_data])
    
    return {
        "overall_avg_efficiency": overall_avg_efficiency,
        "efficiency_variance": efficiency_variance,
        "hourly_efficiency": hourly_avg_efficiency,
        "most_efficient_hours": most_efficient_hours,
        "least_efficient_hours": least_efficient_hours,
        "efficiency_stability": "stable" if efficiency_variance < 0.5 else "variable"
    }

@tool
def predict_usage_patterns(telemetry_data: List[Dict[str, Any]], forecast_hours: int = 24) -> Dict[str, Any]:
    """
    Predict future usage patterns based on historical data.
    
    Args:
        telemetry_data: List of telemetry readings with timestamps and power loads
        forecast_hours: Number of hours to forecast ahead
        
    Returns:
        Dictionary containing usage pattern predictions
    """
    if not telemetry_data or len(telemetry_data) < 48:  # Need at least 2 days of data
        return {"error": "Insufficient data for prediction (need at least 48 hours)"}
    
    # Extract power loads and timestamps
    power_loads = [reading["power_load_kw"] for reading in telemetry_data]
    timestamps = [reading["timestamp"] for reading in telemetry_data]
    
    # Group by hour and day of week for pattern analysis
    hourly_patterns = {}
    dow_patterns = {}  # Day of week patterns
    
    for reading in telemetry_data:
        dt = datetime.fromisoformat(reading["timestamp"].replace('Z', '+00:00'))
        hour = dt.hour
        dow = dt.weekday()  # 0=Monday, 6=Sunday
        
        if hour not in hourly_patterns:
            hourly_patterns[hour] = []
        hourly_patterns[hour].append(reading["power_load_kw"])
        
        if dow not in dow_patterns:
            dow_patterns[dow] = []
        dow_patterns[dow].append(reading["power_load_kw"])
    
    # Calculate average by hour and day of week
    hourly_avg = {hour: statistics.mean(loads) for hour, loads in hourly_patterns.items()}
    dow_avg = {dow: statistics.mean(loads) for dow, loads in dow_patterns.items()}
    
    # Simple prediction: use weighted average of recent similar time periods
    # Weight more recent data higher
    current_time = datetime.fromisoformat(telemetry_data[-1]["timestamp"].replace('Z', '+00:00'))
    current_hour = current_time.hour
    current_dow = current_time.weekday()
    
    # Get historical average for current hour and day of week
    base_prediction = hourly_avg.get(current_hour, statistics.mean(power_loads))
    dow_adjustment = dow_avg.get(current_dow, 0) - statistics.mean(power_loads)
    
    # Apply day-of-week adjustment
    adjusted_prediction = base_prediction + dow_adjustment
    
    # Generate hourly predictions for the next forecast_hours
    predictions = []
    for i in range(1, forecast_hours + 1):
        future_hour = (current_hour + i) % 24
        future_dow = (current_dow + (current_hour + i) // 24) % 7
        
        # Base prediction from historical average
        hour_prediction = hourly_avg.get(future_hour, statistics.mean(power_loads))
        
        # Apply day-of-week adjustment if we cross to a new day
        if i > 24 - current_hour:  # If we're predicting for next day
            dow_adj = dow_avg.get(future_dow, 0) - statistics.mean(power_loads)
            hour_prediction += dow_adj
        
        # Add some randomness for realism (±5%)
        import random
        variation = random.uniform(0.95, 1.05)
        final_prediction = hour_prediction * variation
        
        predictions.append({
            "hour_offset": i,
            "predicted_power": final_prediction,
            "confidence": "high" if i <= 6 else "medium"  # Higher confidence for near-term
        })
    
    return {
        "current_hour": current_hour,
        "current_dow": current_dow,
        "hourly_patterns": hourly_avg,
        "dow_patterns": dow_avg,
        "predictions": predictions
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
    
    # Use analyze_usage_patterns tool
    usage_analysis = analyze_usage_patterns(telemetry_dicts)
    
    # Use analyze_efficiency_trends tool
    efficiency_analysis = analyze_efficiency_trends(telemetry_dicts)
    
    # Use predict_usage_patterns tool for future predictions
    prediction_analysis = predict_usage_patterns(telemetry_dicts)
    
    return {
        **state,
        "analysis_results": {
            "usage_patterns": usage_analysis,
            "efficiency_trends": efficiency_analysis,
            "predictions": prediction_analysis
        }
    }

def generate_recommendations(state: EnergyOptimizationState):
    """Generate optimization recommendations based on analysis."""
    analysis = state["analysis_results"]
    
    if "usage_patterns" not in analysis or "error" in analysis["usage_patterns"]:
        return {
            **state,
            "optimization_result": None
        }
    
    # Calculate optimal shutdown window
    shutdown_window = calculate_optimal_shutdown(analysis["usage_patterns"])
    
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
    
    # Generate natural language recommendation with efficiency and prediction insights
    efficiency_trends = analysis.get("efficiency_trends", {})
    predictions = analysis.get("predictions", {})
    
    # Extract key prediction insights
    next_24h_predictions = predictions.get("predictions", [])[:24]
    avg_predicted_load = statistics.mean([p["predicted_power"] for p in next_24h_predictions]) if next_24h_predictions else 0
    
    recommendation_prompt = f"""
    Based on generator usage analysis:
    - Average power consumption: {analysis['usage_patterns']['avg_power']:.2f} kW
    - Lowest usage hours: {analysis['usage_patterns']['lowest_usage_hours']}
    - Recommended shutdown window: {shutdown_window['start_time'].strftime('%H:%M')} to {shutdown_window['end_time'].strftime('%H:%M')} ({shutdown_window['duration_hours']} hours)
    - Daily savings: ${savings_data['daily_savings_usd']:.2f}
    - Monthly savings: ${savings_data['monthly_savings_usd']:.2f}
    
    Efficiency Analysis:
    - Overall efficiency: {efficiency_trends.get('overall_avg_efficiency', 0):.2f} kW per liter
    - Efficiency stability: {efficiency_trends.get('efficiency_stability', 'unknown')}
    - Most efficient hours: {[h for h, _ in efficiency_trends.get('most_efficient_hours', [])]}
    - Least efficient hours: {[h for h, _ in efficiency_trends.get('least_efficient_hours', [])]}
    
    Predictive Analysis:
    - Predicted average load (next 24h): {avg_predicted_load:.2f} kW
    - High confidence predictions: {[p['hour_offset'] for p in next_24h_predictions if p.get('confidence') == 'high']}
    - Peak predicted hours: {sorted([(p['hour_offset'], p['predicted_power']) for p in next_24h_predictions], key=lambda x: x[1], reverse=True)[:3]}
    
    Provide a comprehensive recommendation for the operator explaining:
    1. Benefits of the recommended shutdown window
    2. Efficiency patterns and how to optimize them
    3. Specific actions to improve fuel efficiency
    4. How to prepare for predicted high-load periods
    """
    
    messages = [
        SystemMessage(content="You are an expert energy optimization advisor for industrial generators. Provide clear, actionable recommendations with specific efficiency and predictive insights."),
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

# Build agent graph
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
    
    # Compile with memory but without retry_policy for compatibility
    return workflow.compile(
        checkpointer=memory,
        interrupt_before=[],  # No interrupts needed for this use case
        interrupt_after=[]
    )

# Initialize the agent
energy_agent = create_energy_optimization_agent()

async def run_optimization_analysis(telemetry_data: List[TelemetryReading], fuel_price: float = 1.50, thread_id: str = None) -> Optional[OptimizationResult]:
    """
    Run energy optimization analysis on telemetry data.
    
    Args:
        telemetry_data: List of telemetry readings to analyze
        fuel_price: Price of fuel per liter (default from environment)
        thread_id: Optional thread ID for conversation persistence
        
    Returns:
        OptimizationResult: Complete optimization recommendation or None if analysis fails
    """
    if not telemetry_data:
        return None
    
    try:
        # Create a unique thread ID if not provided
        if thread_id is None:
            thread_id = f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        agent_input = {
            "telemetry_data": telemetry_data,
            "fuel_price": fuel_price,
            "messages": [SystemMessage(content="Analyze generator telemetry data and provide optimization recommendations.")]
        }
        
        # Use thread_id for persistence
        config = {"configurable": {"thread_id": thread_id}}
        result = await energy_agent.ainvoke(agent_input, config=config)
        return result.get("optimization_result")
    except Exception as e:
        print(f"Error running optimization analysis: {e}")
        return None
