"""
Utilities for optimizing caching and data processing across the app.
"""

# Standard library imports
import functools
import hashlib
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

# Third-party imports
import pandas as pd
import streamlit as st

# Local imports
from utils.config import CACHE_TTL_LONG, CACHE_TTL_MEDIUM, CACHE_TTL_SHORT, CACHE_TTL_VERY_LONG

# Type variables for generic function signatures
T = TypeVar("T")
R = TypeVar("R")

# In-memory cache
_MEMORY_CACHE: Dict[str, Tuple[Any, float, float]] = {}


def generate_cache_key(*args: Any, **kwargs: Any) -> str:
    """
    Generate a consistent cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        String hash representing the cache key
    """
    # Convert args and kwargs to strings and concatenate
    args_str = str(args)
    kwargs_str = str(sorted(kwargs.items()))

    # Generate hash
    key = hashlib.md5((args_str + kwargs_str).encode()).hexdigest()
    return key


def memory_cache(ttl: float = CACHE_TTL_SHORT) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Custom in-memory cache decorator with TTL.

    Args:
        ttl: Time-to-live in seconds (defaults to CACHE_TTL_SHORT from config)

    Returns:
        Decorated function with caching
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate key
            cache_key = f"{func.__name__}:{generate_cache_key(*args, **kwargs)}"

            # Get current time
            current_time = time.time()

            # Check if in cache and not expired
            if cache_key in _MEMORY_CACHE:
                result, timestamp, result_ttl = _MEMORY_CACHE[cache_key]
                if current_time - timestamp < result_ttl:
                    logging.debug(f"Cache hit for {func.__name__}")
                    return cast(T, result)
                else:
                    logging.debug(f"Cache expired for {func.__name__}")

            # Execute function and store result
            result = func(*args, **kwargs)
            _MEMORY_CACHE[cache_key] = (result, current_time, ttl)
            logging.debug(f"Cache miss for {func.__name__}, result stored")

            # Clean up expired entries occasionally (1% chance)
            if hash(cache_key) % 100 == 0:
                cleanup_memory_cache()

            return result

        return wrapper

    return decorator


def cleanup_memory_cache() -> None:
    """
    Remove expired entries from the memory cache.
    """
    current_time = time.time()
    expired_keys = []

    # Find expired entries
    for key, (_, timestamp, ttl) in _MEMORY_CACHE.items():
        if current_time - timestamp >= ttl:
            expired_keys.append(key)

    # Remove expired entries
    for key in expired_keys:
        del _MEMORY_CACHE[key]

    if expired_keys:
        logging.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


def clear_memory_cache() -> None:
    """
    Clear the entire memory cache.
    """
    global _MEMORY_CACHE
    _MEMORY_CACHE = {}
    logging.info("Memory cache cleared")


def optimize_dataframe(
    df: pd.DataFrame, category_threshold: float = 0.5, downcast_numeric: bool = True
) -> pd.DataFrame:
    """
    Optimize a DataFrame's memory usage by choosing appropriate dtypes.

    Args:
        df: DataFrame to optimize
        category_threshold: Percentage threshold for converting string columns to category
        downcast_numeric: Whether to downcast numeric columns

    Returns:
        Optimized DataFrame
    """
    if df.empty:
        return df

    result = df.copy()

    # Process object columns
    for col in df.select_dtypes(include=["object"]).columns:
        num_unique = df[col].nunique()
        num_total = len(df)

        # If unique values are less than threshold percentage, convert to category
        if num_unique / num_total < category_threshold:
            result[col] = df[col].astype("category")

    # Downcast numeric columns
    if downcast_numeric:
        for col in df.select_dtypes(include=["int", "float"]).columns:
            if df[col].dtype == "int64":
                result[col] = pd.to_numeric(df[col], downcast="integer")
            elif df[col].dtype == "float64":
                result[col] = pd.to_numeric(df[col], downcast="float")

    return result


def batch_process_dataframe(
    df: pd.DataFrame, func: Callable[[pd.DataFrame], pd.DataFrame], batch_size: int = 10000
) -> pd.DataFrame:
    """
    Process a large DataFrame in batches to avoid memory issues.

    Args:
        df: Input DataFrame
        func: Function to apply to each batch
        batch_size: Size of each batch

    Returns:
        Processed DataFrame
    """
    if len(df) <= batch_size:
        return func(df)

    # Process in batches
    results = []
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i : i + batch_size].copy()
        processed = func(batch)
        results.append(processed)

    # Combine results
    return pd.concat(results, ignore_index=True)


def parallel_apply(
    df: pd.DataFrame, func: Callable[[Any], R], column: str, n_jobs: int = -1
) -> pd.Series:
    """
    Apply a function to a DataFrame column in parallel.

    Args:
        df: Input DataFrame
        func: Function to apply
        column: Column name to apply function to
        n_jobs: Number of parallel jobs (-1 for all cores)

    Returns:
        Series with results
    """
    try:
        from joblib import Parallel, delayed

        # Process in parallel
        results = Parallel(n_jobs=n_jobs)(delayed(func)(x) for x in df[column])

        return pd.Series(results, index=df.index)

    except ImportError:
        # Fall back to standard apply if joblib not available
        logging.warning("joblib not available, falling back to standard apply")
        return df[column].apply(func)
