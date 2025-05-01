"""
Sidebar components for the Stablecoin Dashboard.
"""
import os
import logging
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple, Callable

from utils.config import LOGO_PATH


def create_sidebar(
    title: str = "Izun Dashboard",
    navigation_options: Optional[List[str]] = None,
    contact_info: Optional[str] = None,
    logo_path: Optional[str] = None
) -> str:
    """
    Create a consistent sidebar with navigation and branding.
    
    Args:
        title: Title for the sidebar
        navigation_options: List of navigation options
        contact_info: Contact information to display
        logo_path: Path to the logo image
        
    Returns:
        Selected navigation option
    """
    with st.sidebar:
        # Display logo if available
        logo_path = logo_path or LOGO_PATH
        
        if logo_path and os.path.exists(logo_path):
            try:
                st.image(logo_path)
            except Exception as e:
                st.warning(f"Could not display logo image: {e}")
                logging.warning(f"Failed to display logo: {e}")
        elif logo_path:
            st.warning(f"Logo file '{logo_path}' not found.")
            logging.warning(f"Logo file not found at: {logo_path}")

        # Title
        st.title(title)

        # Navigation options
        if navigation_options is None:
            navigation_options = [
                "Overview",
                "Stablecoin Yields",
                "Stablecoin Analytics",
                "Pool Yields",
                "Pool Yield Analytics",
            ]
            
        choice = st.radio("Navigation", navigation_options, key="nav_choice")
        
        # Contact info
        if contact_info:
            st.info(contact_info)
            
        return choice


def add_sidebar_filter(
    label: str,
    options: List[Any],
    default_index: int = 0,
    key_suffix: str = "",
    help_text: str = ""
) -> Any:
    """
    Add a filter to the sidebar.
    
    Args:
        label: Label for the filter
        options: List of options
        default_index: Index of the default option
        key_suffix: Suffix for the filter key
        help_text: Help text for the filter
        
    Returns:
        Selected option
    """
    with st.sidebar:
        return st.selectbox(
            label=label,
            options=options,
            index=default_index,
            key=f"sidebar_{key_suffix}",
            help=help_text
        )


def add_sidebar_slider(
    label: str,
    min_value: float,
    max_value: float,
    value: float,
    step: float = 1.0,
    key_suffix: str = "",
    help_text: str = "",
    format: str = "%f"
) -> float:
    """
    Add a slider to the sidebar.
    
    Args:
        label: Label for the slider
        min_value: Minimum value
        max_value: Maximum value
        value: Default value
        step: Step size
        key_suffix: Suffix for the slider key
        help_text: Help text for the slider
        format: Format string for the value
        
    Returns:
        Selected value
    """
    with st.sidebar:
        return st.slider(
            label=label,
            min_value=min_value,
            max_value=max_value,
            value=value,
            step=step,
            key=f"sidebar_slider_{key_suffix}",
            help=help_text,
            format=format
        )


def add_sidebar_expander(
    label: str,
    expanded: bool = False
) -> st.expander:
    """
    Add an expander to the sidebar.
    
    Args:
        label: Label for the expander
        expanded: Whether the expander is expanded by default
        
    Returns:
        Expander object
    """
    with st.sidebar:
        return st.expander(label, expanded=expanded)


def add_sidebar_divider() -> None:
    """Add a divider to the sidebar."""
    with st.sidebar:
        st.divider()


def add_sidebar_info(message: str) -> None:
    """
    Add an info message to the sidebar.
    
    Args:
        message: Message to display
    """
    with st.sidebar:
        st.info(message)