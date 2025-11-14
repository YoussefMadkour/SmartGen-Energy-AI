# AI Agent Architecture for Energy Optimization

## Overview

This document describes the AI agent implementation for the SmartGen Energy AI system, which analyzes generator telemetry data and provides optimization recommendations to reduce fuel costs through strategic shutdown windows.

## Agent Type: Custom LangGraph Agent

We chose a custom LangGraph agent for this implementation because:

1. **Domain-Specific Requirements**: Generator optimization requires specialized knowledge about power usage patterns, fuel efficiency, and operational constraints that generic agents don't address.
2. **Real-time Data Processing**: The system processes continuous telemetry data streams, requiring an agent that can handle time-series analysis.
3. **Explainable Decision Making**: Industrial applications require transparent reasoning for safety and compliance.
4. **Complex Multi-Step Analysis**: The optimization process involves multiple sequential steps that benefit from LangGraph's state management.

## Architecture Components

### 1. Agent State Management

```python
class EnergyOptimizationState(TypedDict):
    telemetry_data: List[TelemetryReading]
    analysis_results: Dict[str, Any]
    optimization_result: Optional[OptimizationResult]
    messages: List[Any]
    fuel_price: float
```

The state maintains all information needed throughout the analysis process, allowing each node to access and update shared data.

### 2. Agent Tools

#### fetch_usage_profile Tool
```python
@tool
def analyze_usage_patterns(telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
```

**Purpose**: Retrieves and analyzes historical power load data to identify usage patterns.

**Implementation**:
- Extracts power loads and timestamps from telemetry data
- Calculates basic statistics (average, min, max)
- Groups data by hour to identify daily patterns
- Identifies lowest usage hours (potential shutdown windows)
- Returns comprehensive usage analysis

#### compute_shutdown_window Tool
```python
@tool
def calculate_optimal_shutdown(usage_analysis: Dict[str, Any]) -> Dict[str, Any]:
```

**Purpose**: Implements a sliding window algorithm to find the optimal shutdown period with minimum load.

**Implementation**:
- Analyzes lowest usage hours from usage patterns
- Finds consecutive hours for optimal shutdown window
- Handles edge cases (e.g., windows that cross midnight)
- Calculates start/end times and duration
- Returns structured shutdown window recommendation

#### estimate_savings Tool
```python
@tool
def calculate_savings(shutdown_window: Dict[str, Any], fuel_price: float, avg_fuel_consumption: float) -> Dict[str, Any]:
```

**Purpose**: Calculates projected cost savings from the recommended shutdown window.

**Implementation**:
- Calculates fuel saved per day based on shutdown duration
- Computes daily and monthly cost savings using fuel price
- Returns structured savings data

### 3. LLM Integration

We configured OpenAI's GPT-4 model with specific parameters:

```python
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4"),
    temperature=0.1
)
```

**Low Temperature (0.1)**: Ensures consistent, analytical responses rather than creative variations.

### 4. LLM Prompt Engineering

The system uses a carefully crafted prompt to generate natural language recommendations:

```python
recommendation_prompt = f"""
Based on generator usage analysis:
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
```

**Prompt Strategy**:
- **System Message**: Establishes the AI's role as an expert energy advisor
- **Contextual Data**: Provides all relevant metrics and calculations
- **Clear Instructions**: Asks for concise, actionable recommendations
- **Domain Focus**: Tailored to industrial generator operations

### 5. Agent Orchestration

The agent follows a sequential workflow implemented as nodes in a directed graph:

```python
def create_energy_optimization_agent():
    workflow = StateGraph(EnergyOptimizationState)
    
    # Add nodes
    workflow.add_node("analyze_data", analyze_data)
    workflow.add_node("generate_recommendations", generate_recommendations)
    
    # Add edges
    workflow.add_edge(START, "analyze_data")
    workflow.add_edge("analyze_data", "generate_recommendations")
    workflow.add_edge("generate_recommendations", END)
    
    return workflow.compile()
```

**Workflow Steps**:
1. **Data Analysis**: Processes telemetry data to identify usage patterns
2. **Recommendation Generation**: Calculates optimal shutdown windows and savings
3. **Result Compilation**: Creates structured optimization result with natural language explanation

## Integration with Existing System

### Backend Integration

1. **New Service**: `agent_service.py` contains the LangGraph agent implementation
2. **API Endpoint**: Added `/api/metrics/optimize` endpoint to `metrics_service.py`
3. **Dependencies**: Updated `requirements.txt` to include `langgraph==0.2.16`
4. **Main Application**: Updated `main.py` to import the agent service

### Frontend Integration

1. **OptimizationPanel Component**: Displays AI recommendations in a user-friendly format
2. **Real-time Updates**: Fetches new recommendations periodically
3. **Error Handling**: Gracefully handles API errors and loading states
4. **Responsive Design**: Works on desktop and mobile devices

## Data Flow

1. **Telemetry Collection**: IoT simulator generates realistic generator data
2. **Data Storage**: Telemetry readings stored in SQLite database
3. **Analysis Trigger**: Frontend requests optimization via API
4. **Agent Processing**: LangGraph agent analyzes data using tools
5. **Recommendation Delivery**: Structured results returned to frontend
6. **Visualization**: Results displayed with charts and natural language explanation

## Benefits of This Implementation

1. **Modular Design**: Each component has a single responsibility
2. **Transparent Reasoning**: Tool-based approach provides explainable decisions
3. **Real-time Processing**: Handles continuous data streams efficiently
4. **Domain Specificity**: Tailored to industrial generator optimization
5. **Extensible**: Easy to add new analysis tools or modify the workflow
6. **Production Ready**: Includes error handling, validation, and monitoring

## Future Enhancements

1. **Machine Learning**: Replace statistical analysis with ML models for better pattern recognition
2. **Multi-Generator Support**: Extend to optimize multiple generators simultaneously
3. **Historical Learning**: Incorporate feedback from implemented recommendations
4. **Advanced Constraints**: Add operational constraints (maintenance schedules, etc.)
5. **Predictive Analysis**: Forecast future usage patterns for proactive optimization

## Conclusion

This custom LangGraph agent implementation provides a robust, extensible foundation for generator optimization that delivers clear business value through fuel cost savings while maintaining operational safety and efficiency.
