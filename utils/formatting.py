"""
Utility functions for formatting values in the dashboard.
"""
import pandas as pd
import numpy as np
import re

def format_tvl(tvl):
    """Formats TVL number into a human-readable string (B, M, K)."""
    if pd.isna(tvl) or not isinstance(tvl, (int, float)) or tvl == 0:
        return "N/A"
    if abs(tvl) >= 1_000_000_000:
        return f"${tvl / 1_000_000_000:.2f}B"
    if abs(tvl) >= 1_000_000:
        return f"${tvl / 1_000_000:.2f}M"
    if abs(tvl) >= 1_000:
        return f"${tvl / 1_000:.1f}K"
    return f"${tvl:.0f}"

def format_apy(apy):
    """Formats APY number into a percentage string."""
    if pd.isna(apy) or not isinstance(apy, (int, float)):
        return "N/A"
    return f"{apy:.2f}%"

def format_metadata(value):
    """Returns 'N/A' if value is NaN, None, or empty string, otherwise returns the value."""
    return value if pd.notna(value) and value != '' else "N/A"

def format_staked_proportion(value):
    """Handles specific formatting for staked proportion, treating '?' and empty strings as N/A."""
    if pd.isna(value) or value in ['', '?']:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:.2f}%"
    return str(value)

def parse_yield(yield_str):
    """Parses yield string ('X.XX%') into a float. Returns NaN on failure."""
    if not isinstance(yield_str, str) or yield_str == 'N/A':
        return np.nan
    try:
        return float(yield_str.strip().replace('%', ''))
    except (ValueError, AttributeError):
        return np.nan

def parse_tvl(tvl_str):
    """Parses TVL string ('$X.XX[B/M/K]') into a float USD value. Returns NaN on failure."""
    if not isinstance(tvl_str, str) or tvl_str == 'N/A':
        return np.nan
    try:
        tvl_str = tvl_str.strip().replace('$', '').replace(',', '').lower()
        multiplier = 1
        if tvl_str.endswith('b'):
            multiplier = 1_000_000_000
            tvl_str = tvl_str[:-1]
        elif tvl_str.endswith('m'):
            multiplier = 1_000_000
            tvl_str = tvl_str[:-1]
        elif tvl_str.endswith('k'):
            multiplier = 1_000
            tvl_str = tvl_str[:-1]

        return float(tvl_str) * multiplier
    except (ValueError, AttributeError):
        return np.nan

def categorize_stablecoin_by_strategy(desc):
    """Categorizes stablecoins based on their yield strategies from description text."""
    desc = str(desc).lower()
    if pd.isna(desc) or desc == 'n/a' or desc == '':
        return 'Unknown/Other'
    if 't-bill' in desc or 'treasury' in desc or 'rwa' in desc:
        return 'RWA/Treasury-backed'
    if 'delta neutral' in desc or 'funding' in desc or 'cash & carry' in desc or 'delta neutra' in desc or 'perps funding' in desc:
        return 'Delta Neutral/Arb'
    if 'restaking' in desc:
        return 'Restaking'
    if 'native protocol yield' in desc or 'protocol revenue' in desc or 'interest paid by' in desc or 'safety module' in desc or 'native dex' in desc or 'sky savings rate' in desc:
        return 'Protocol Native Yield'
    if 'loan' in desc or 'lend' in desc or 'borrower interest' in desc or 'morpho vault' in desc:
        return 'Lending/Borrowing'
    if 'index' in desc or 'diversified' in desc or 'mixture' in desc:
        return 'Index/Diversified'
    if 'farming' in desc or '3rd party defi' in desc or 'across defi bluechips' in desc:
        return 'External DeFi Farming'
    if 'institutional trading' in desc:
        return 'Trading Strategy'
    if 'swap fees' in desc:
        return 'LP Fees'
    if 'option' in desc:
        return 'Options/Structured Product'
    return 'Unknown/Other'