"""
API utility functions for fetching data from external sources.
"""

# Standard library imports
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party imports
import pandas as pd
import requests
import streamlit as st

# Local imports
from utils.config import (
    API_DELAY,
    API_RETRIES,
    API_TIMEOUT,
    CACHE_TTL_LONG,
    CACHE_TTL_MEDIUM,
    DEFILLAMA_PROTOCOL_API_URL,
    DEFILLAMA_STABLECOINS_API_URL,
    DEFILLAMA_YIELDS_API_URL,
    RATE_LIMIT_REQUESTS_PER_MINUTE,
    RATE_LIMIT_WINDOW_SECONDS,
)
from utils.error_handling import create_error_dataframe, handle_api_error

# Import types the module needs (for proper type checking)
from utils.security import (
    InvalidURLError,
    RateLimitExceededError,
    ValidationError,
    rate_limit_request,
    sanitize_url,
    secure_request_headers,
    validate_api_response,
)

# Rate limiting storage
RATE_LIMIT_STORE: Dict[str, Dict[str, int]] = {}


def fetch_data_with_retries(
    url: str,
    timeout: int = API_TIMEOUT,
    retries: int = API_RETRIES,
    delay: int = API_DELAY,
    error_message: str = "API request failed",
    expected_keys: Optional[List[str]] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Generic function to fetch data from an API with retry logic and proper error handling.

    Args:
        url: The API endpoint URL
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        delay: Delay between retries in seconds
        error_message: Custom error message prefix
        expected_keys: List of keys expected in the response
        api_key: Optional API key for authenticated requests
        api_secret: Optional API secret for signed requests

    Returns:
        JSON response as dict or None if all requests fail

    Raises:
        Various SecurityError subclasses that are caught and handled
    """
    try:
        # Sanitize and validate the URL
        sanitized_url = sanitize_url(url)
        if sanitized_url != url:
            logging.info(f"URL sanitized from {url} to {sanitized_url}")
            url = sanitized_url

        # Check rate limits before proceeding
        rate_limit_request(url, RATE_LIMIT_STORE)

        # Generate secure headers
        headers = secure_request_headers(api_key, api_secret)

    except SecurityError as e:
        # Handle security-related errors before making any requests
        handle_api_error(e, f"Security error when preparing request to {url}", logging.ERROR)
        return None

    attempt = 0
    last_error = None

    while attempt < retries:
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()  # Raises HTTPError for bad responses

            # Parse the response
            response_data = response.json()

            # Validate the response structure
            validate_api_response(response_data, expected_keys)

            return response_data

        except ValidationError as e:
            # Validation errors are likely to be consistent across retries,
            # but we might try again in case it was a transient issue
            attempt += 1
            last_error = e
            logging.warning(f"API response validation failed (Attempt {attempt}/{retries}): {e}")

            if attempt < retries:
                st.warning(f"Invalid API response format. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                handle_api_error(
                    e,
                    f"Failed to validate response from {url} after {retries} attempts",
                    logging.ERROR,
                )
                return None

        except requests.exceptions.RequestException as e:
            # Network or HTTP errors might be transient
            attempt += 1
            last_error = e
            logging.warning(f"{error_message} (Attempt {attempt}/{retries}): {e}")

            if attempt < retries:
                st.warning(f"Request failed. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                handle_api_error(
                    e, f"Failed to fetch data from {url} after {retries} attempts", logging.ERROR
                )
                return None

        except json.JSONDecodeError as e:
            # JSON parsing errors usually indicate bad response data
            attempt += 1
            last_error = e
            logging.warning(f"JSON parsing error (Attempt {attempt}/{retries}): {e}")

            if attempt < retries:
                st.warning(f"Invalid JSON response. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                handle_api_error(
                    e, f"Failed to parse JSON from {url} after {retries} attempts", logging.ERROR
                )
                return None

        except Exception as e:
            # Catch any other unexpected errors
            attempt += 1
            last_error = e
            logging.error(f"Unexpected error (Attempt {attempt}/{retries}): {e}")

            if attempt < retries:
                st.warning(f"Unexpected error occurred. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                handle_api_error(
                    e,
                    f"Unexpected error when fetching data from {url}",
                    logging.ERROR,
                    show_traceback=True,
                )
                return None

    # If we reach here, all retries failed but we might not have raised a final error
    if last_error:
        handle_api_error(
            last_error, f"Failed to fetch data from {url} after {retries} attempts", logging.ERROR
        )

    return None


@st.cache_data(ttl=CACHE_TTL_LONG)
def get_stablecoin_metadata(retries: int = API_RETRIES, delay: int = API_DELAY) -> pd.DataFrame:
    """
    Fetches stablecoin metadata from DefiLlama API with caching.

    Args:
        retries: Number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        DataFrame with stablecoin metadata or empty DataFrame on error
    """
    data = fetch_data_with_retries(
        DEFILLAMA_STABLECOINS_API_URL,
        retries=retries,
        delay=delay,
        error_message="Stablecoin Metadata API request failed",
        expected_keys=["peggedAssets"],
    )

    if not data or "peggedAssets" not in data or not isinstance(data["peggedAssets"], list):
        if data:
            st.error("Unexpected Stablecoin Metadata API response format.")
            logging.error(f"Stablecoin Metadata API response format error: {data}")
        return pd.DataFrame()

    try:
        meta_df = pd.DataFrame(data["peggedAssets"])
        cols_to_keep = ["symbol", "name", "pegMechanism", "pegType"]
        meta_df = meta_df[[col for col in cols_to_keep if col in meta_df.columns]].copy()
        meta_df["join_symbol"] = meta_df["symbol"].str.lower()

        return meta_df

    except Exception as e:
        handle_api_error(
            e, "Error processing stablecoin metadata", logging.ERROR, show_traceback=True
        )
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL_MEDIUM)
def fetch_defillama_yield_pools(
    retries: int = API_RETRIES, delay: int = API_DELAY
) -> Optional[pd.DataFrame]:
    """
    Fetches and performs initial processing of yield pool data from DefiLlama.

    Args:
        retries: Number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Processed DataFrame with yield pool data or None on error
    """
    logging.info("Fetching yield pool data from DefiLlama...")

    data = fetch_data_with_retries(
        DEFILLAMA_YIELDS_API_URL,
        retries=retries,
        delay=delay,
        error_message="Yield Pool API request failed",
        expected_keys=["data"],
    )

    if not data or "data" not in data or not isinstance(data["data"], list):
        if data:
            error_msg = "Unexpected Yield Pool API response format."
            st.error(error_msg)
            logging.error(f"{error_msg} Response: {data}")
        return None

    try:
        df = pd.DataFrame(data["data"])
        logging.info(f"Initial pool count: {len(df)}")

        # Ensure required columns exist and have proper types
        required_columns = {
            "stablecoin": False,
            "symbol": "",
            "tvlUsd": pd.NA,
            "apy": pd.NA,
            "project": "Unknown",
            "chain": "Unknown",
        }

        # Add missing columns with default values
        for col, default in required_columns.items():
            if col not in df.columns:
                df[col] = default

        # Convert column types appropriately with defensive error handling
        try:
            df["stablecoin"] = (
                pd.to_numeric(df["stablecoin"], errors="coerce").fillna(0).astype(bool)
            )
        except Exception:
            logging.warning("Error converting 'stablecoin' column to boolean, using default False")
            df["stablecoin"] = False

        df["symbol"] = df["symbol"].astype(str)
        df["project"] = df["project"].astype(str)
        df["chain"] = df["chain"].astype(str)

        try:
            df["tvlUsd"] = pd.to_numeric(df["tvlUsd"], errors="coerce")
        except Exception:
            logging.warning("Error converting 'tvlUsd' column to numeric, using NaN")
            df["tvlUsd"] = pd.NA

        try:
            df["apy"] = pd.to_numeric(df["apy"], errors="coerce")
        except Exception:
            logging.warning("Error converting 'apy' column to numeric, using NaN")
            df["apy"] = pd.NA

        df["join_symbol"] = df["symbol"].str.lower()

        return df

    except Exception as e:
        error_msg = "Error processing yield pool data"
        handle_api_error(e, error_msg, logging.ERROR, show_traceback=True)
        return None
