"""
Pool Yield Analytics page of the dashboard.
"""
import logging
import pandas as pd
import streamlit as st

from utils.config import TARGET_YIELD_ASSET_SYMBOLS_LOWER, DEFAULT_MIN_TVL_USD
from utils.api import get_stablecoin_metadata
from utils.data_processing import get_analytics_data
from utils.formatting import format_tvl
from utils.visualization import (
    create_apy_distribution_histogram,
    create_tvl_vs_apy_scatter,
    create_top_yield_plot,
    create_top_projects_by_tvl
)


def show_pool_yield_analytics():
    """Display the pool yield analytics page with visualizations."""
    st.title("Pool Yield Analytics")
    st.write("Visualizations based on the broader stablecoin and yield-asset pool data from API (Default TVL > $10M).")

    # Get stablecoin metadata for joining
    stablecoin_metadata_api = get_stablecoin_metadata()
    
    # Use default TVL filter for analytics
    analytics_min_tvl_api = DEFAULT_MIN_TVL_USD
    st.info(f"Analytics based on API pools with TVL > {format_tvl(analytics_min_tvl_api)}")

    # Get analytics data
    analytics_data_api = get_analytics_data(
        analytics_min_tvl_api, 
        TARGET_YIELD_ASSET_SYMBOLS_LOWER, 
        stablecoin_metadata_api
    )

    # Check if data is valid
    data_valid_analytics_api = not (isinstance(analytics_data_api, pd.DataFrame) and
                                  any(col in analytics_data_api.columns for col in 
                                     ['error', 'warning', 'warning_tvl']))

    if data_valid_analytics_api and not analytics_data_api.empty:
        # APY Distribution
        st.subheader("APY Distribution")
        try:
            if 'APY' in analytics_data_api.columns:
                fig_hist = create_apy_distribution_histogram(analytics_data_api)
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.warning("Pool Analytics: APY column not found in API data.")
        except Exception as e:
            st.warning(f"Pool Analytics: Could not generate APY Distribution plot: {e}")

        # TVL vs. APY
        st.divider()
        st.subheader("TVL vs. APY")
        try:
            if 'TVL_USD' in analytics_data_api.columns and 'APY' in analytics_data_api.columns:
                hover_cols = ['Chain', 'Project', 'Issuer/Name', 'Type (Peg)', 'Type (Peg Mechanism)']
                fig_scatter = create_tvl_vs_apy_scatter(
                    analytics_data_api,
                    color_column='Project',
                    hover_name='Asset Symbol',
                    hover_data_columns=hover_cols
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.warning("Pool Analytics: Required columns missing for TVL vs APY plot.")
        except Exception as e:
            st.warning(f"Pool Analytics: Could not generate TVL vs APY plot: {e}")

        # Top Pools by APY
        st.divider()
        st.subheader("Top Pools by APY")
        try:
            if 'APY' in analytics_data_api.columns and 'Asset Symbol' in analytics_data_api.columns:
                hover_cols = ['Project', 'Chain', 'TVL_USD', 'Type (Peg)', 'Issuer/Name']
                fig_bar_apy = create_top_yield_plot(
                    analytics_data_api,
                    top_n=20,
                    color_column=None,
                    hover_data_columns=hover_cols
                )
                st.plotly_chart(fig_bar_apy, use_container_width=True)
            else:
                st.warning("Pool Analytics: Required columns missing for Top APY plot.")
        except Exception as e:
            st.warning(f"Pool Analytics: Could not generate Top Pools by APY plot: {e}")

        # Top 10 Projects by TVL
        st.divider()
        st.subheader("Top 10 Projects by TVL")
        try:
            if 'Project' in analytics_data_api.columns and 'TVL_USD' in analytics_data_api.columns:
                fig_top_tvl = create_top_projects_by_tvl(analytics_data_api, top_n=10)
                st.plotly_chart(fig_top_tvl, use_container_width=True)
            else:
                st.warning("Pool Analytics: Cannot generate Top 10 Projects plot: Missing columns (API Data).")
        except Exception as e:
            st.warning(f"Pool Analytics: Could not generate Top Projects by TVL plot: {e}")

    # Handle error states
    elif isinstance(analytics_data_api, pd.DataFrame) and 'error' in analytics_data_api.columns:
        st.error(f"Pool Analytics: Failed to fetch or process API data - {analytics_data_api['error'].iloc[0]}")
    elif isinstance(analytics_data_api, pd.DataFrame) and ('warning' in analytics_data_api.columns or 'warning_tvl' in analytics_data_api.columns):
        if 'warning' in analytics_data_api.columns:
            st.warning(f"Pool Analytics: {analytics_data_api['warning'].iloc[0]}. No API pools matched base criteria.")
        elif 'warning_tvl' in analytics_data_api.columns:
            st.warning(f"Pool Analytics: {analytics_data_api['warning_tvl'].iloc[0]}. No API pools matched TVL criteria.")
        st.warning("Pool Analytics (API) may be incomplete due to data limitations.")
    else:
        st.warning("No API data available to generate pool yield analytics plots.")