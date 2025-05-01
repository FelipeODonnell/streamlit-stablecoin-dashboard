"""
Security utilities for API interactions and data handling.
"""
# Standard library imports
import base64
import hashlib
import hmac
import json
import logging
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Union

# Local imports
from utils.config import RATE_LIMIT_REQUESTS_PER_MINUTE, RATE_LIMIT_WINDOW_SECONDS

# Custom exceptions for better error handling
class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass

class InvalidURLError(SecurityError):
    """Exception raised for invalid or malformed URLs."""
    pass

class RateLimitExceededError(SecurityError):
    """Exception raised when API rate limits are exceeded."""
    pass

class ValidationError(SecurityError):
    """Exception raised when data validation fails."""
    pass

# Make exceptions available at module level for imports
__all__ = [
    'SecurityError',
    'InvalidURLError',
    'RateLimitExceededError',
    'ValidationError'
]

def sanitize_url(url: str) -> str:
    """
    Sanitize a URL to ensure it's valid and safe.
    
    Args:
        url: The URL to sanitize
        
    Returns:
        Sanitized URL with https scheme
        
    Raises:
        InvalidURLError: If the URL is invalid or cannot be sanitized
    """
    if not url:
        raise InvalidURLError("URL cannot be empty")
        
    try:
        # Parse the URL
        parsed = urllib.parse.urlparse(url)
        
        # Check for minimal required components
        if not parsed.netloc:
            raise InvalidURLError(f"Invalid URL format: {url}")
        
        # Ensure the scheme is https
        if parsed.scheme != 'https':
            original_scheme = parsed.scheme
            parsed = parsed._replace(scheme='https')
            logging.warning(f"URL scheme changed from {original_scheme} to https for security")
        
        # Sanitize path components
        path_components = parsed.path.split('/')
        sanitized_components = [urllib.parse.quote(component) for component in path_components]
        sanitized_path = '/'.join(sanitized_components)
        
        parsed = parsed._replace(path=sanitized_path)
        
        # Return the sanitized URL
        return urllib.parse.urlunparse(parsed)
    except Exception as e:
        raise InvalidURLError(f"Failed to sanitize URL: {str(e)}") from e


def validate_api_response(
    response_data: Any, 
    expected_keys: Optional[List[str]] = None
) -> bool:
    """
    Validate that an API response contains expected data and structure.
    
    Args:
        response_data: The API response data to validate
        expected_keys: List of keys that should be present in the response
        
    Returns:
        True if the response is valid
        
    Raises:
        ValidationError: If the response data fails validation
    """
    # Check for None response
    if response_data is None:
        error_msg = "API response is None"
        logging.error(error_msg)
        raise ValidationError(error_msg)
    
    # If expected keys were provided, check for their presence
    if expected_keys:
        missing_keys = []
        for key in expected_keys:
            if key not in response_data:
                missing_keys.append(key)
                
        if missing_keys:
            error_msg = f"Expected keys missing from API response: {', '.join(missing_keys)}"
            logging.error(error_msg)
            raise ValidationError(error_msg)
    
    return True


def rate_limit_request(
    url: str, 
    rate_limit_storage: Dict[str, Dict[str, int]]
) -> bool:
    """
    Check if a request to a URL should be rate limited.
    
    Args:
        url: The URL being requested
        rate_limit_storage: Dictionary storing rate limit information
        
    Returns:
        True if the request should proceed
        
    Raises:
        RateLimitExceededError: If the rate limit has been exceeded
        InvalidURLError: If the URL is invalid
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        
        if not domain:
            raise InvalidURLError(f"Invalid URL: {url}")
            
    except Exception as e:
        if not isinstance(e, InvalidURLError):
            raise InvalidURLError(f"Failed to parse URL for rate limiting: {str(e)}") from e
        raise
        
    current_time = int(time.time())
    
    # Initialize rate limiting for this domain if not exists
    if domain not in rate_limit_storage:
        rate_limit_storage[domain] = {
            'last_request': current_time,
            'count': 0,
            'window_start': current_time
        }
    
    domain_limits = rate_limit_storage[domain]
    
    # Reset count if window has passed
    if current_time - domain_limits['window_start'] > RATE_LIMIT_WINDOW_SECONDS:
        domain_limits['count'] = 0
        domain_limits['window_start'] = current_time
    
    # Check if we've exceeded rate limit
    if domain_limits['count'] >= RATE_LIMIT_REQUESTS_PER_MINUTE:
        error_msg = f"Rate limit exceeded for {domain}, request blocked"
        logging.warning(error_msg)
        raise RateLimitExceededError(error_msg)
    
    # Update request count and last request time
    domain_limits['count'] += 1
    domain_limits['last_request'] = current_time
    
    return True


def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_str: The input string to sanitize
        
    Returns:
        Sanitized string
    """
    # Remove any potentially dangerous characters
    sanitized = re.sub(r'[<>"\'&;]', '', input_str)
    
    # Limit length to prevent DOS attacks
    return sanitized[:1000]  # Limit to 1000 chars


def sanitize_filter_value(value: Any) -> Any:
    """
    Sanitize a value used for filtering data.
    
    Args:
        value: The filter value to sanitize
        
    Returns:
        Sanitized filter value
    """
    if isinstance(value, str):
        return sanitize_input(value)
    elif isinstance(value, (int, float, bool)) or value is None:
        return value
    elif isinstance(value, list):
        return [sanitize_filter_value(item) for item in value]
    elif isinstance(value, dict):
        return {sanitize_input(k): sanitize_filter_value(v) for k, v in value.items()}
    else:
        # For other types, convert to string and sanitize
        return sanitize_input(str(value))


def hash_sensitive_data(data: str) -> str:
    """
    Hash sensitive data for logging or storing.
    
    Args:
        data: The sensitive data to hash
        
    Returns:
        Hashed representation of the data
    """
    return hashlib.sha256(data.encode()).hexdigest()


def secure_request_headers(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate secure headers for API requests.
    
    Args:
        api_key: Optional API key for authentication
        api_secret: Optional API secret for signing requests
        
    Returns:
        Dictionary of headers to add to the request
    """
    headers = {
        'User-Agent': 'IzunDashboard/1.0',
        'Accept': 'application/json',
        'X-Request-ID': hashlib.md5(str(time.time()).encode()).hexdigest()
    }
    
    if api_key:
        headers['X-API-Key'] = api_key
        
        # If an API secret is provided, create a signed request
        if api_secret:
            timestamp = str(int(time.time()))
            message = timestamp + api_key
            
            # Create signature using HMAC-SHA256
            signature = hmac.new(
                api_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            headers['X-Timestamp'] = timestamp
            headers['X-Signature'] = signature
    
    return headers