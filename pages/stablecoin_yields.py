"""
Stablecoin Yields page of the dashboard.
"""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from utils.config import MANUAL_STABLECOIN_DATA
from utils.data_processing import get_stablecoin_yields_data
from utils.formatting import categorize_stablecoin_by_strategy


def show_stablecoin_yields():
    """Display the stablecoin yields page."""
    st.title("Stablecoin Yields")
    st.caption("Data manually updated on a weekly basis")

    # Get the stablecoin yield data
    stablecoin_yield_data = get_stablecoin_yields_data(MANUAL_STABLECOIN_DATA)

    # Check if data is valid
    data_valid = not (
        isinstance(stablecoin_yield_data, pd.DataFrame)
        and ("error" in stablecoin_yield_data.columns or "warning" in stablecoin_yield_data.columns)
    )

    filtered_data = pd.DataFrame()
    options_projects = ["All"]
    options_strategy = ["All"]

    if data_valid and not stablecoin_yield_data.empty:
        filtered_data = stablecoin_yield_data.copy()

        # Add strategy type column for filtering
        filtered_data["Strategy Type"] = filtered_data["Description"].apply(
            categorize_stablecoin_by_strategy
        )

        # Get list of projects and strategies for filters
        if "Project" in filtered_data.columns:
            options_projects.extend(sorted(filtered_data["Project"].dropna().unique()))
        if "Strategy Type" in filtered_data.columns:
            options_strategy.extend(sorted(filtered_data["Strategy Type"].dropna().unique()))

        # Create filters UI
        st.subheader("Filters")
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_ticker = st.text_input(
                "Filter by Ticker Contains",
                placeholder="e.g. susde",
                key="stable_yields_ticker_filter",
            )
        with col2:
            filter_project = st.selectbox(
                "Filter by Project",
                options=options_projects,
                index=0,
                key="stable_yields_project_filter",
            )
        with col3:
            filter_strategy = st.selectbox(
                "Filter by Strategy Type",
                options=options_strategy,
                index=0,
                key="stable_yields_strategy_filter",
            )

        # Apply filters
        if filter_ticker:
            if "Ticker" in filtered_data.columns:
                filtered_data = filtered_data[
                    filtered_data["Ticker"].str.lower().str.contains(filter_ticker.lower())
                ]
            else:
                st.error("Filtering failed: 'Ticker' column not found.")

        if filter_project != "All":
            if "Project" in filtered_data.columns:
                filtered_data = filtered_data[filtered_data["Project"] == filter_project]
            else:
                st.warning("Cannot filter by project: 'Project' column missing.")

        if filter_strategy != "All":
            if "Strategy Type" in filtered_data.columns:
                filtered_data = filtered_data[filtered_data["Strategy Type"] == filter_strategy]
            else:
                st.warning("Cannot filter by strategy: 'Strategy Type' column missing.")

    # Handle error states
    elif (
        isinstance(stablecoin_yield_data, pd.DataFrame) and "error" in stablecoin_yield_data.columns
    ):
        st.error(f"Failed to load stablecoin yield data: {stablecoin_yield_data['error'].iloc[0]}")
    elif (
        isinstance(stablecoin_yield_data, pd.DataFrame)
        and "warning" in stablecoin_yield_data.columns
    ):
        st.warning(
            f"Could not load all stablecoin yield data: {stablecoin_yield_data['warning'].iloc[0]}"
        )
    elif stablecoin_yield_data.empty:
        st.warning("No data loaded for stablecoin yields (Manual data might be empty).")

    # Display divider before data table
    st.divider()

    # Display the filtered data
    if not filtered_data.empty and data_valid:
        st.info(f"Displaying {len(filtered_data)} target stablecoins.")

        display_cols = ["Project", "Ticker", "Yield", "TVL", "Description"]
        cols_to_display = [col for col in display_cols if col in filtered_data.columns]

        # Configure column displays
        column_config = {
            "Project": st.column_config.TextColumn(
                "Project", help="Associated project/protocol (manual)"
            ),
            "Ticker": st.column_config.TextColumn(
                "Ticker", help="Yield-bearing asset symbol (manual)"
            ),
            "Yield": st.column_config.TextColumn("Yield", help="Manually entered APY (%)"),
            "TVL": st.column_config.TextColumn("TVL", help="Manually entered TVL (USD)"),
            "Description": st.column_config.TextColumn(
                "Description", help="Yield source description (manual)"
            ),
            "Staked Proportion": st.column_config.TextColumn(
                "Staked %", help="Staked proportion (manual)"
            ),
        }

        column_config_filtered = {k: v for k, v in column_config.items() if k in cols_to_display}

        st.dataframe(
            filtered_data[cols_to_display],
            column_config=column_config_filtered,
            hide_index=True,
            use_container_width=True,
        )

    # Handle empty results after filtering
    elif (
        filtered_data.empty
        and (filter_ticker or filter_project != "All" or filter_strategy != "All")
        and data_valid
    ):
        st.warning("No stablecoin yields match the selected filter criteria.")
    elif filtered_data.empty and not data_valid:
        pass  # Error already displayed above
    elif filtered_data.empty:
        st.warning("No data available for stablecoin yields overview.")
