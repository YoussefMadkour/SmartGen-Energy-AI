"""
Unit tests for optimization agent tools.

These tests verify the core logic of the optimization agent:
- Internal computation functions work correctly
- Savings calculations are accurate
- Shutdown window algorithm finds optimal periods
"""

import pytest
from datetime import datetime, timedelta
from optimization_agent import _estimate_savings_raw, _compute_shutdown_window_raw


def test_estimate_savings_basic():
    """Test basic savings calculation."""
    result = _estimate_savings_raw(
        duration_hours=4.0,
        avg_fuel_rate_lph=45.0
    )
    
    # Verify structure
    assert "fuel_saved_liters" in result
    assert "daily_savings_usd" in result
    assert "monthly_savings_usd" in result
    
    # Verify calculations (assuming $1.50/liter from env)
    # 4 hours * 45 L/h = 180 liters
    # 180 L * $1.50 = $270 daily
    # $270 * 30 = $8100 monthly
    assert result["fuel_saved_liters"] == 180.0
    assert result["daily_savings_usd"] == 270.0
    assert result["monthly_savings_usd"] == 8100.0


def test_estimate_savings_different_duration():
    """Test savings with different duration."""
    result = _estimate_savings_raw(
        duration_hours=6.0,
        avg_fuel_rate_lph=30.0
    )
    
    # 6 hours * 30 L/h = 180 liters
    # 180 L * $1.50 = $270 daily
    # $270 * 30 = $8100 monthly
    assert result["fuel_saved_liters"] == 180.0
    assert result["daily_savings_usd"] == 270.0
    assert result["monthly_savings_usd"] == 8100.0


def test_compute_shutdown_window_basic():
    """Test shutdown window computation with synthetic data."""
    # Create 24 hours of data with clear minimum period
    base_time = datetime(2025, 11, 14, 0, 0, 0)
    usage_data = []
    
    for hour in range(24):
        timestamp = base_time + timedelta(hours=hour)
        # Low load from 2 AM to 6 AM (hours 2-5)
        if 2 <= hour < 6:
            power_load = 50.0
            fuel_rate = 15.0
        else:
            power_load = 150.0
            fuel_rate = 45.0
        
        usage_data.append((
            timestamp.isoformat(),
            power_load,
            fuel_rate
        ))
    
    result = _compute_shutdown_window_raw(
        usage_data,
        min_hours=2,
        max_hours=8
    )
    
    # Verify structure
    assert "start_time" in result
    assert "end_time" in result
    assert "duration_hours" in result
    assert "avg_power_load_kw" in result
    assert "avg_fuel_consumption_lph" in result
    
    # Verify it found the low-load period
    start = datetime.fromisoformat(result["start_time"])
    assert start.hour == 2  # Should start at 2 AM
    
    # Verify average load is low
    assert result["avg_power_load_kw"] < 100.0


def test_compute_shutdown_window_respects_constraints():
    """Test that window respects min/max duration constraints."""
    base_time = datetime(2025, 11, 14, 0, 0, 0)
    usage_data = []
    
    # Create uniform data
    for hour in range(24):
        timestamp = base_time + timedelta(hours=hour)
        usage_data.append((
            timestamp.isoformat(),
            100.0,
            30.0
        ))
    
    result = _compute_shutdown_window_raw(
        usage_data,
        min_hours=3,
        max_hours=5
    )
    
    # Duration should be between 3 and 5 hours
    assert 3.0 <= result["duration_hours"] <= 5.0


if __name__ == "__main__":
    # Run tests manually
    print("Running optimization agent tests...")
    
    try:
        test_estimate_savings_basic()
        print("✓ test_estimate_savings_basic passed")
        
        test_estimate_savings_different_duration()
        print("✓ test_estimate_savings_different_duration passed")
        
        test_compute_shutdown_window_basic()
        print("✓ test_compute_shutdown_window_basic passed")
        
        test_compute_shutdown_window_respects_constraints()
        print("✓ test_compute_shutdown_window_respects_constraints passed")
        
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
