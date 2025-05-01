"""
Utility functions for consistent error handling and logging across the application.
"""
# Standard library imports
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

# Third-party imports
import pandas as pd
import streamlit as st

# We'll move these imports inside the functions that need them to avoid circular imports
# from utils.security import SecurityError, ValidationError

# Type variables for generic function signatures
T = TypeVar('T')
R = TypeVar('R')

# Define application-specific exceptions
class AppError(Exception):
    """Base exception for application-specific errors."""
    pass

class DataError(AppError):
    """Exception raised for data-related errors."""
    pass

class UIError(AppError):
    """Exception raised for UI-related errors."""
    pass

class ConfigError(AppError):
    """Exception raised for configuration-related errors."""
    pass

def handle_api_error(
    error: Exception, 
    error_message: str, 
    log_level: int = logging.ERROR,
    show_traceback: bool = False
) -> None:
    """
    Consistently handle and log API errors with special handling for custom exceptions.
    
    Args:
        error: The exception that was raised
        error_message: Human-readable error message to display/log
        log_level: Logging level to use
        show_traceback: Whether to include the traceback in the log
    """
    # Import here to avoid circular imports
    from utils.security import SecurityError, ValidationError
    
    # Adjust log level and message based on exception type
    if isinstance(error, SecurityError):
        # Security errors are always logged at ERROR level
        log_level = logging.ERROR
        user_message = "A security-related error occurred. Please try again or contact support."
        detailed_message = f"{error_message}: {str(error)}"
    elif isinstance(error, ValidationError):
        # Validation errors are typically warnings
        if log_level == logging.ERROR:
            log_level = logging.WARNING
        user_message = f"Validation error: {str(error)}"
        detailed_message = f"{error_message}: {str(error)}"
    elif isinstance(error, DataError):
        user_message = f"Data processing error: {str(error)}"
        detailed_message = f"{error_message}: {str(error)}"
    elif isinstance(error, UIError):
        user_message = f"UI error: {str(error)}"
        detailed_message = f"{error_message}: {str(error)}"
    elif isinstance(error, ConfigError):
        user_message = "Configuration error. Please contact support."
        detailed_message = f"{error_message}: {str(error)}"
    else:
        # For other exceptions, use the normal format
        user_message = f"{error_message}: {str(error)}"
        detailed_message = user_message
    
    # Log the error with appropriate level
    if log_level == logging.ERROR:
        if show_traceback:
            logging.error(detailed_message + "\n" + traceback.format_exc())
        else:
            logging.error(detailed_message)
    elif log_level == logging.WARNING:
        if show_traceback:
            logging.warning(detailed_message + "\n" + traceback.format_exc())
        else:
            logging.warning(detailed_message)
    elif log_level == logging.INFO:
        logging.info(detailed_message)
    else:
        logging.log(log_level, detailed_message)
    
    # Display error message to user
    if log_level == logging.ERROR:
        st.error(user_message)
    elif log_level == logging.WARNING:
        st.warning(user_message)
    else:
        st.info(user_message)


def create_error_dataframe(
    error_type: str, 
    message: str, 
    details: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Create a consistent error response DataFrame.
    
    Args:
        error_type: Type of error (e.g., 'error', 'warning', 'warning_tvl')
        message: Error message to include
        details: Optional dictionary of additional error details
        
    Returns:
        DataFrame with error information
    """
    error_data = {error_type: [message]}
    
    if details:
        for key, value in details.items():
            error_data[f"{error_type}_{key}"] = [value]
            
    return pd.DataFrame(error_data)


def safe_execute(
    func: Callable[..., R],
    *args,
    error_message: str = "Operation failed",
    default_return: Optional[T] = None,
    log_level: int = logging.ERROR,
    show_traceback: bool = False,
    **kwargs
) -> Union[R, T]:
    """
    Execute a function safely, handling any exceptions.
    
    Args:
        func: Function to execute
        *args: Args to pass to the function
        error_message: Message to display/log on error
        default_return: Value to return on error
        log_level: Logging level to use for errors
        show_traceback: Whether to show traceback in logs
        **kwargs: Keyword args to pass to the function
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_api_error(e, error_message, log_level, show_traceback)
        return cast(T, default_return)


def validate_dataframe(
    df: Optional[pd.DataFrame],
    required_columns: Optional[List[str]] = None,
    min_rows: int = 1,
    error_prefix: str = "Data validation failed",
    raise_exception: bool = False
) -> bool:
    """
    Validate that a DataFrame meets basic requirements.
    
    Args:
        df: DataFrame to validate
        required_columns: List of column names that must be present
        min_rows: Minimum number of rows required
        error_prefix: Prefix for error messages
        raise_exception: Whether to raise an exception on validation failure
        
    Returns:
        True if valid, False otherwise (with appropriate error messages shown)
        
    Raises:
        DataError: If validation fails and raise_exception is True
    """
    if df is None:
        error_msg = f"{error_prefix}: DataFrame is None"
        if raise_exception:
            raise DataError(error_msg)
        st.error(error_msg)
        return False
        
    if df.empty:
        error_msg = f"{error_prefix}: DataFrame is empty"
        if raise_exception:
            raise DataError(error_msg)
        st.warning(error_msg)
        return False
        
    if len(df) < min_rows:
        error_msg = f"{error_prefix}: DataFrame has fewer than {min_rows} rows"
        if raise_exception:
            raise DataError(error_msg)
        st.warning(error_msg)
        return False
        
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"{error_prefix}: Missing required columns: {', '.join(missing_columns)}"
            if raise_exception:
                raise DataError(error_msg)
            st.error(error_msg)
            return False
            
    return True