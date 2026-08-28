import pytest
from app.services.predictive_intelligence.utils import simple_moving_average, linear_trend_forecast

def test_simple_moving_average():
    data = [10.0, 20.0, 30.0]
    result = simple_moving_average(data, window=3)
    assert result == 20.0
    
    result2 = simple_moving_average(data, window=2)
    assert result2 == 25.0

def test_linear_trend_forecast():
    # Perfect linear trend y = 10x + 10
    # [10, 20, 30] -> next should be 40
    data = [10.0, 20.0, 30.0]
    result = linear_trend_forecast(data, periods_ahead=1)
    assert abs(result - 40.0) < 0.001
    
    # 2 periods ahead -> 50
    result2 = linear_trend_forecast(data, periods_ahead=2)
    assert abs(result2 - 50.0) < 0.001
