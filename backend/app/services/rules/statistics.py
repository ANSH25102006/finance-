import math
from typing import List

def get_percentile(data: List[float], percentile: float) -> float:
    """
    Calculate the percentile of a list of numeric values using linear interpolation.
    """
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (percentile / 100.0)
    idx_floor = int(k)
    idx_ceil = idx_floor + 1
    if idx_ceil < len(sorted_data):
        return sorted_data[idx_floor] + (sorted_data[idx_ceil] - sorted_data[idx_floor]) * (k - idx_floor)
    return sorted_data[idx_floor]

def calculate_iqr_threshold(data: List[float]) -> float:
    """
    Calculate the IQR threshold for outliers: Q3 + 1.5 * IQR.
    Returns infinity if there are fewer than 5 data points to prevent false outlier classification.
    """
    if len(data) < 5:
        return float('inf')
    q1 = get_percentile(data, 25.0)
    q3 = get_percentile(data, 75.0)
    iqr = q3 - q1
    return q3 + 1.5 * iqr

def calculate_std_dev_threshold(data: List[float], num_std_dev: float = 2.0) -> float:
    """
    Calculate the standard deviation outlier threshold: mean + num_std_dev * std_dev.
    """
    if len(data) < 2:
        return float('inf')
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
    std_dev = math.sqrt(variance)
    return mean + num_std_dev * std_dev
