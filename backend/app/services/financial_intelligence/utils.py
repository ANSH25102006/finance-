# ============================================================
#  utils.py — Shared helpers for the Financial Intelligence Engine
# ============================================================

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta
from typing import Any


# ------------------------------------------------------------------ #
# Date helpers
# ------------------------------------------------------------------ #

def month_start(year: int, month: int) -> date:
    """Return the first day of the given month."""
    return date(year, month, 1)


def month_end(year: int, month: int) -> date:
    """Return the last day of the given month."""
    _, last = calendar.monthrange(year, month)
    return date(year, month, last)


def prev_month(year: int, month: int) -> tuple[int, int]:
    """Return (year, month) for the month immediately before the given one."""
    if month == 1:
        return year - 1, 12
    return year, month - 1


def months_ago(today: date, n: int) -> tuple[int, int]:
    """Return (year, month) that is exactly n months before today."""
    month = today.month - n
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return year, month


def last_n_months(today: date, n: int) -> list[tuple[int, int]]:
    """Return a list of (year, month) tuples for the last n months (inclusive of current)."""
    result = []
    for i in range(n - 1, -1, -1):
        result.append(months_ago(today, i))
    return result


def is_weekend(d: date) -> bool:
    """Return True if the date falls on Saturday (5) or Sunday (6)."""
    return d.weekday() >= 5


# ------------------------------------------------------------------ #
# Transaction grouping helpers
# ------------------------------------------------------------------ #

def group_by_month(transactions: list[Any]) -> dict[tuple[int, int], list[Any]]:
    """Group a list of Transaction ORM objects by (year, month)."""
    result: dict[tuple[int, int], list[Any]] = defaultdict(list)
    for tx in transactions:
        key = (tx.transaction_date.year, tx.transaction_date.month)
        result[key].append(tx)
    return dict(result)


def group_by_category(transactions: list[Any]) -> dict[str, list[Any]]:
    """Group transactions by category name. Transactions with no category go into '__uncategorised__'."""
    result: dict[str, list[Any]] = defaultdict(list)
    for tx in transactions:
        cat_name = tx.category.name if tx.category else "__uncategorised__"
        result[cat_name].append(tx)
    return dict(result)


def group_by_merchant(transactions: list[Any]) -> dict[str, list[Any]]:
    """Group transactions by merchant name. Blanks go into '__unknown__'."""
    result: dict[str, list[Any]] = defaultdict(list)
    for tx in transactions:
        merchant = (tx.merchant or "").strip() or "__unknown__"
        result[merchant].append(tx)
    return dict(result)


# ------------------------------------------------------------------ #
# Aggregation helpers
# ------------------------------------------------------------------ #

def total_amount(transactions: list[Any]) -> float:
    """Sum the amounts of a list of Transaction objects."""
    return float(sum(float(tx.amount) for tx in transactions))


def filter_by_type(transactions: list[Any], tx_type: str) -> list[Any]:
    """Return only transactions matching the given type ('income' or 'expense')."""
    return [tx for tx in transactions if tx.transaction_type == tx_type]


def filter_by_month(transactions: list[Any], year: int, month: int) -> list[Any]:
    """Return transactions whose transaction_date falls in the given month."""
    return [
        tx for tx in transactions
        if tx.transaction_date.year == year and tx.transaction_date.month == month
    ]


def filter_by_date_range(transactions: list[Any], start: date, end: date) -> list[Any]:
    """Return transactions within [start, end] inclusive."""
    return [tx for tx in transactions if start <= tx.transaction_date <= end]


# ------------------------------------------------------------------ #
# Statistical helpers
# ------------------------------------------------------------------ #

def safe_pct_change(old: float, new: float) -> float:
    """
    Return percentage change from old to new.
    Returns 0.0 if old is zero to avoid ZeroDivisionError.
    """
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100.0


def average(values: list[float]) -> float:
    """Return the arithmetic mean, or 0.0 for an empty list."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def median(values: list[float]) -> float:
    """Return the median of a list, or 0.0 for empty."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    mid = len(sorted_vals) // 2
    if len(sorted_vals) % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


# ------------------------------------------------------------------ #
# Trend detection helpers
# ------------------------------------------------------------------ #

def detect_consecutive_direction(values: list[float], direction: str = "up", min_streak: int = 3) -> bool:
    """
    Return True if the last `min_streak` values form a consecutive increase
    (direction='up') or decrease (direction='down').

    Values are expected in chronological order (oldest first).
    """
    if len(values) < min_streak:
        return False
    tail = values[-(min_streak):]
    if direction == "up":
        return all(tail[i] < tail[i + 1] for i in range(len(tail) - 1))
    else:  # "down"
        return all(tail[i] > tail[i + 1] for i in range(len(tail) - 1))


def month_spending_series(
    transactions: list[Any],
    months: list[tuple[int, int]],
    tx_type: str = "expense",
) -> list[float]:
    """
    Return a list of total amounts per month, in the order of `months`.
    Missing months default to 0.0.
    """
    by_month = group_by_month(filter_by_type(transactions, tx_type))
    return [total_amount(by_month.get(ym, [])) for ym in months]


# ------------------------------------------------------------------ #
# Formatting helpers
# ------------------------------------------------------------------ #

def fmt_currency(amount: float, symbol: str = "₹") -> str:
    """Format a float as a currency string with comma separators."""
    return f"{symbol}{amount:,.0f}"


def fmt_pct(value: float) -> str:
    """Format a float as a percentage string with one decimal place."""
    return f"{value:.1f}%"
