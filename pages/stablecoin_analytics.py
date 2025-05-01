"""
Stablecoin Analytics page of the dashboard.
"""

import logging

import pandas as pd
import streamlit as st

from utils.config import MANUAL_STABLECOIN_DATA
from utils.data_processing import get_enhanced_analytics_data
from utils.visualization import (
    create_avg_yield_by_strategy_plot,
    create_strategy_distribution_pie,
    create_top_yield_plot,
    create_tvl_vs_apy_scatter,
)


def show_stablecoin_analytics():
    """Display the stablecoin analytics page with visualizations."""
    st.title("Stablecoin Analytics")
    st.caption("Analytics derived from data in 'Stablecoin Yields' section.")

    # Get the enhanced analytics data
    enhanced_analytics_data = get_enhanced_analytics_data(MANUAL_STABLECOIN_DATA)

    # Check if data is valid
    data_valid = not (
        isinstance(enhanced_analytics_data, pd.DataFrame)
        and any(col in enhanced_analytics_data.columns for col in ["error", "warning"])
    )

    if data_valid and not enhanced_analytics_data.empty:
        # Top Stablecoins by Yield
        st.subheader("Top Stablecoins by Yield")
        try:
            if (
                "APY" in enhanced_analytics_data.columns
                and "Asset Symbol" in enhanced_analytics_data.columns
            ):
                hover_cols = ["Project", "TVL_USD", "Staked Proportion", "Description"]
                fig_top_yield = create_top_yield_plot(
                    enhanced_analytics_data,
                    top_n=20,
                    color_column="Strategy Type",
                    hover_data_columns=hover_cols,
                )
                st.plotly_chart(fig_top_yield, use_container_width=True)
            else:
                st.warning("Required columns (APY, Asset Symbol) not found for Top Yield plot.")
        except Exception as e:
            st.warning(f"Could not generate Top Yield plot: {e}")
            logging.error(f"Error in Top Yield plot: {e}")

        # Distribution by Strategy Type
        st.divider()
        st.subheader("Distribution by Strategy Type")
        try:
            if "Strategy Type" in enhanced_analytics_data.columns:
                fig_strategy_pie = create_strategy_distribution_pie(enhanced_analytics_data)
                st.plotly_chart(fig_strategy_pie, use_container_width=True)
            else:
                st.warning("Strategy Type information not available for distribution plot.")
        except Exception as e:
            st.warning(f"Could not generate Strategy Distribution plot: {e}")
            logging.error(f"Error in Strategy Distribution plot: {e}")

        # Average Yield by Strategy Type
        st.divider()
        st.subheader("Average Yield by Strategy Type")
        try:
            if (
                "Strategy Type" in enhanced_analytics_data.columns
                and "APY" in enhanced_analytics_data.columns
            ):
                fig_strategy_yield = create_avg_yield_by_strategy_plot(enhanced_analytics_data)
                st.plotly_chart(fig_strategy_yield, use_container_width=True)
            else:
                st.warning("Strategy Type or APY information not available for average yield plot.")
        except Exception as e:
            st.warning(f"Could not generate Average Yield plot: {e}")
            logging.error(f"Error in Average Yield plot: {e}")

        # TVL vs. APY
        st.divider()
        st.subheader("TVL vs. APY")
        try:
            if (
                "TVL_USD" in enhanced_analytics_data.columns
                and "APY" in enhanced_analytics_data.columns
            ):
                hover_cols = ["Strategy Type", "Description", "Staked Proportion"]
                fig_scatter_tvl_apy = create_tvl_vs_apy_scatter(
                    enhanced_analytics_data,
                    color_column="Strategy Type",
                    hover_name="Asset Symbol",
                    hover_data_columns=hover_cols,
                )
                st.plotly_chart(fig_scatter_tvl_apy, use_container_width=True)
            else:
                st.warning(
                    "Required columns (TVL_USD, APY, Project, Asset Symbol) not found for scatter plot."
                )
        except Exception as e:
            st.warning(f"Could not generate TVL vs APY plot: {e}")
            logging.error(f"Error in Stablecoin Analytics TVL vs APY plot: {e}")

    # Handle error states
    elif (
        isinstance(enhanced_analytics_data, pd.DataFrame)
        and "error" in enhanced_analytics_data.columns
    ):
        st.error(
            f"Stablecoin Analytics: Failed to process data - {enhanced_analytics_data['error'].iloc[0]}"
        )
    elif (
        isinstance(enhanced_analytics_data, pd.DataFrame)
        and "warning" in enhanced_analytics_data.columns
    ):
        st.warning(f"Stablecoin Analytics: {enhanced_analytics_data['warning'].iloc[0]}")
        st.warning("Analytics may be incomplete.")
    else:
        st.warning(
            "No data available to generate stablecoin analytics plots (Data might be empty or filtered out)."
        )
