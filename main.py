"""
Streamlit Stablecoin Dashboard - Izun Partners

A dashboard for tracking and analyzing stablecoin yields and pools.
"""

# Standard library imports
import logging
import os
from typing import Dict, List, Optional

# Third-party imports
import pandas as pd
import streamlit as st

# Page imports
from pages.overview import show_overview
from pages.pool_yield_analytics import show_pool_yield_analytics
from pages.pool_yields import show_pool_yields
from pages.stablecoin_analytics import show_stablecoin_analytics
from pages.stablecoin_yields import show_stablecoin_yields

# Local imports
from utils.config import CONTACT_INFO, DEFAULT_NAVIGATION_OPTIONS, LOGO_PATH, TITLE
from utils.style_guide import apply_ui_theme

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Set page config with dark/light mode support
st.set_page_config(
    layout="wide",
    page_title=TITLE,
    page_icon="💰",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/your-username/streamlit-stablecoin-dashboard/issues",
        "Report a bug": "https://github.com/your-username/streamlit-stablecoin-dashboard/issues",
        "About": f"# {TITLE}\nA dashboard for tracking and analyzing stablecoin yields and pools.",
    },
)

# Hide Streamlit's default menu and footer
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def main() -> None:
    """Main entry point for the Streamlit dashboard."""
    # Apply consistent UI styling with dark mode support
    apply_ui_theme()

    # Import here to avoid circular imports
    from components.sidebar import create_sidebar

    # Create sidebar navigation using config values
    choice = create_sidebar(
        title="Izun Dashboard",
        #navigation_options=DEFAULT_NAVIGATION_OPTIONS,
        contact_info=CONTACT_INFO,
        logo_path=LOGO_PATH,
    )

    # Display the selected page
    if choice == "Overview":
        show_overview()
    elif choice == "Stablecoin Yields":
        show_stablecoin_yields()
    elif choice == "Stablecoin Analytics":
        show_stablecoin_analytics()
    elif choice == "Pool Yields":
        show_pool_yields()
    elif choice == "Pool Yield Analytics":
        show_pool_yield_analytics()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logging.exception("Unhandled exception in main application:")
        st.stop()
