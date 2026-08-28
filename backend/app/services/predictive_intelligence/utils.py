# ============================================================
#  utils.py — Statistical utility functions for predictions
# ============================================================

from datetime import date
from typing import Any
import calendar

def simple_moving_average(values: list[float], window: int) -> float:
    """Calculate the simple moving average of the last `window` values."""
    if not values:
        return 0.0
    recent = values[-window:]
    return sum(recent) / len(recent)

def weighted_moving_average(values: list[float], weights: list[float]) -> float:
    """Calculate the weighted moving average. Weights should sum to 1."""
    if not values or not weights:
        return 0.0
    # Apply weights to the most recent values
    recent = values[-len(weights):]
    w = weights[-len(recent):]
    
    # Normalize weights if we don't have enough data points
    w_sum = sum(w)
    if w_sum == 0:
        return 0.0
        
    return sum(v * (wt / w_sum) for v, wt in zip(recent, w))

def linear_trend_forecast(values: list[float], periods_ahead: int) -> float:
    """
    Very simple linear regression forecast.
    y = mx + b
    Returns the forecasted value `periods_ahead` from the end.
    """
    n = len(values)
    if n < 2:
        return values[0] if values else 0.0
        
    sum_x = sum(range(n))
    sum_y = sum(values)
    sum_x_sq = sum(x*x for x in range(n))
    sum_xy = sum(x*y for x, y in enumerate(values))
    
    denominator = (n * sum_x_sq - sum_x * sum_x)
    if denominator == 0:
        return sum_y / n
        
    m = (n * sum_xy - sum_x * sum_y) / denominator
    b = (sum_y - m * sum_x) / n
    
    return m * (n - 1 + periods_ahead) + b

def days_in_current_month(d: date) -> int:
    return calendar.monthrange(d.year, d.month)[1]

def days_remaining_in_month(d: date) -> int:
    return days_in_current_month(d) - d.day
