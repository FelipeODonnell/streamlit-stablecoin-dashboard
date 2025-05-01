"""
Pool Yields page of the dashboard.
"""
import logging
import pandas as pd
import streamlit as st
from datetime import datetime
import pytz

from utils.config import TARGET_YIELD_ASSET_SYMBOLS_LOWER, DEFAULT_MIN_TVL_USD
from utils.api import get_stablecoin_metadata
from utils.data_processing import get_yield_data
from utils.formatting import format_tvl


def show_pool_yields():
    """Display the pool yields page with DeFiLlama data."""
    st.title('Pool Yields')
    
    # Get the current time in London timezone for refresh timestamp
    try:
        london_time = datetime.now(pytz.timezone('Europe/London'))
        refresh_time_str = london_time.strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception:
        refresh_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    st.caption(f"Data sourced from DeFiLlama | Last Refreshed: {refresh_time_str}")

    # Get stablecoin metadata for joining
    stablecoin_metadata = get_stablecoin_metadata()

    # Create filter UI
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns([1, 1.5, 1.5, 1.5])
    
    with col1:
        min_tvl_input = st.number_input(
            label="Minimum Pool TVL (USD)", 
            min_value=0, 
            max_value=10_000_000_000,
            value=DEFAULT_MIN_TVL_USD, 
            step=1_000_000,
            help="Filter pools by minimum Total Value Locked in USD.", 
            format="%d", 
            key="pool_tvl_filter"
        )

    # Get initial data with minimum TVL filter
    initial_yield_data = get_yield_data(min_tvl_input, TARGET_YIELD_ASSET_SYMBOLS_LOWER, stablecoin_metadata)

    # Initialize filter variables
    selected_projects = []
    selected_types = []
    options_projects = ["All"]
    options_types = ["All"]
    filter_symbol_search = ""

    # Check if data is valid
    data_valid = not (isinstance(initial_yield_data, pd.DataFrame) and
                      any(col in initial_yield_data.columns for col in ['error', 'warning', 'warning_tvl']))

    # Prepare filter options if data is valid
    if data_valid and not initial_yield_data.empty:
        try:
            if 'Project' in initial_yield_data.columns:
                options_projects.extend(sorted(initial_yield_data['Project'].dropna().unique()))
            if 'Type (Peg)' in initial_yield_data.columns:
                options_types.extend(sorted(initial_yield_data['Type (Peg)'].dropna().unique()))
        except KeyError as e:
            st.error(f"Pool Yields: Expected column missing for filter options: {e}")
            data_valid = False
        except Exception as e:
            st.error(f"Pool Yields: Error preparing filter options: {e}")
            data_valid = False

    # Create remaining filter inputs
    with col2:
        filter_symbol_search = st.text_input(
            "Filter Symbol Contains", 
            placeholder="e.g. usdc, usde", 
            disabled=not data_valid, 
            key="pool_symbol_filter"
        )
        
    with col3:
        selected_project_filter = st.selectbox(
            "Filter by Project", 
            options=options_projects, 
            index=0, 
            disabled=not data_valid, 
            key="pool_project_filter"
        )
        selected_projects = [] if selected_project_filter == "All" else [selected_project_filter]
        
    with col4:
        selected_type_filter = st.selectbox(
            "Filter by Type (Peg)", 
            options=options_types, 
            index=0, 
            disabled=not data_valid, 
            key="pool_type_filter"
        )
        selected_types = [] if selected_type_filter == "All" else [selected_type_filter]

    # Filter the data based on user selections
    filtered_yield_data = pd.DataFrame()
    if data_valid and not initial_yield_data.empty:
        filtered_yield_data = initial_yield_data.copy()
        try:
            if filter_symbol_search:
                if 'Asset Symbol' in filtered_yield_data.columns:
                    filtered_yield_data = filtered_yield_data[
                        filtered_yield_data['Asset Symbol'].str.lower().str.contains(filter_symbol_search.lower())
                    ]
                else:
                    st.warning("Pool Yields: Cannot filter by symbol: 'Asset Symbol' column missing.")
                    
            if selected_projects:
                if 'Project' in filtered_yield_data.columns:
                    filtered_yield_data = filtered_yield_data[filtered_yield_data['Project'].isin(selected_projects)]
                else:
                    st.warning("Pool Yields: Cannot filter by project: 'Project' column missing.")
                    
            if selected_types:
                if 'Type (Peg)' in filtered_yield_data.columns:
                    filtered_yield_data = filtered_yield_data[filtered_yield_data['Type (Peg)'].isin(selected_types)]
                else:
                    st.warning("Pool Yields: Cannot filter by type: 'Type (Peg)' column missing.")
                    
        except KeyError as e:
            st.error(f"Pool Yields: Error applying filters: Column '{e}' not found.")
            filtered_yield_data = pd.DataFrame()
        except Exception as e:
            st.error(f"Pool Yields: Unexpected error applying filters: {e}")
            filtered_yield_data = pd.DataFrame()

    # Display divider before data table
    st.divider()

    # Handle error states
    if isinstance(initial_yield_data, pd.DataFrame) and 'error' in initial_yield_data.columns:
        st.error(f"Pool Yields Data fetching failed: {initial_yield_data['error'].iloc[0]}. Please try again later.")
    elif isinstance(initial_yield_data, pd.DataFrame) and 'warning' in initial_yield_data.columns:
        st.warning(f"Pool Yields Initial data load issue: {initial_yield_data['warning'].iloc[0]}. No pools matched the base criteria from API.")
    elif isinstance(initial_yield_data, pd.DataFrame) and 'warning_tvl' in initial_yield_data.columns:
        st.warning(f"Pool Yields Initial data load issue: {initial_yield_data['warning_tvl'].iloc[0]}. No pools found matching API criteria with TVL > {format_tvl(min_tvl_input)}.")
    elif not data_valid:
        st.error("Pool Yields: Could not load data or prepare filters correctly.")
    elif filtered_yield_data.empty and (filter_symbol_search or selected_projects or selected_types):
        st.warning("Pool Yields: No pools match the selected filter criteria.")
    elif filtered_yield_data.empty:
        st.warning("Pool Yields: No pool data available after initial filtering.")
    else:
        # Display the filtered data
        st.info(f"Displaying {len(filtered_yield_data)} pools from DefiLlama.")
        
        display_columns = ['Chain', 'Project', 'Asset Symbol', 'APY (%)', 'TVL (USD)', 'Issuer/Name', 'Type (Peg)']
        yield_data_display = filtered_yield_data[[col for col in display_columns if col in filtered_yield_data.columns]]
        
        column_config = {
            "TVL (USD)": st.column_config.TextColumn("TVL (USD)", help="Total Value Locked (Formatted)"),
            "APY (%)": st.column_config.TextColumn("APY (%)", help="Annual Percentage Yield (Formatted)"),
            "Issuer/Name": st.column_config.TextColumn("Issuer/Name", help="Issuing project or name (from metadata)"),
            "Type (Peg)": st.column_config.TextColumn("Type (Peg)", help="Peg type (from metadata)")
        }
        
        st.dataframe(
            yield_data_display, 
            column_config=column_config, 
            hide_index=True, 
            use_container_width=True
        )