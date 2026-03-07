"""
Synapse Test Module
A simple module designed to be optimized by the PlasticityEngine.
Optimized for performance and extended with useful utilities while maintaining API compatibility.
"""

import math
from functools import lru_cache

def slow_calculation(n):
    """Calculate the sum of first (n-1) integers using optimized mathematical formula.

    Args:
        n: Upper bound of the sum (exclusive)

    Returns:
        Sum of integers from 0 to n-1
    """
    if n < 0:
        raise ValueError("Input must be non-negative")
    return n * (n - 1) // 2

@lru_cache(maxsize=128)
def cached_slow_calculation(n):
    """Memoized version of slow_calculation for repeated calls with same inputs."""
    return slow_calculation(n)

def get_metadata():
    """Get module metadata.

    Returns:
        Dictionary containing module version and name
    """
    return {
        "version": "1.1.0",
        "name": "synapse_test",
        "optimizations": ["mathematical_optimization", "memoization"]
    }

def calculate_stats(numbers):
    """Calculate basic statistics for a list of numbers.

    Args:
        numbers: Iterable of numerical values

    Returns:
        Dictionary containing count, sum, mean, min, max, and standard deviation
    """
    if not numbers:
        return {}

    count = len(numbers)
    total = sum(numbers)
    mean = total / count
    min_val = min(numbers)
    max_val = max(numbers)

    variance = sum((x - mean) ** 2 for x in numbers) / count
    std_dev = math.sqrt(variance)

    return {
        "count": count,
        "sum": total,
        "mean": mean,
        "min": min_val,
        "max": max_val,
        "std_dev": std_dev
    }

def is_prime(n):
    """Check if a number is prime.

    Args:
        n: Number to check

    Returns:
        Boolean indicating primality
    """
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    w = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += w
        w = 6 - w
    return True