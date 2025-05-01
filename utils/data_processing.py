"""
Data processing utilities for the stablecoin dashboard.
"""
import logging
import pandas as pd
import numpy as np
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple, Union

from utils.api import fetch_defillama_yield_pools
from utils.formatting import (
    format_tvl, format_apy, format_metadata, format_staked_proportion,
    parse_yield, parse_tvl, categorize_stablecoin_by_strategy
)
from utils.error_handling import create_error_dataframe, handle_api_error
from utils.caching import optimize_dataframe, batch_process_dataframe, parallel_apply

# Constants
DEFAULT_MIN_TVL_USD = 10_000_000

def get_yield_data(
    min_tvl: float,
    target_yield_assets_lower: List[str],
    stablecoin_metadata_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    Processes yield pool data for the Pool Yields table, filtering, merging metadata, and formatting.
    
    Args:
        min_tvl: Minimum TVL filter value
        target_yield_assets_lower: List of target yield asset symbols in lowercase
        stablecoin_metadata_df: DataFrame with stablecoin metadata
        
    Returns:
        DataFrame with processed yield data for display
    """
    base_df = fetch_defillama_yield_pools()

    # Early return cases
    error_return = create_error_dataframe('error', "Data fetch failed")
    warning_return = create_error_dataframe('warning', "No pools matched base criteria")
    warning_tvl_return = create_error_dataframe(
        'warning_tvl', 
        f"No pools matched TVL > {format_tvl(min_tvl)}"
    )

    if base_df is None:
        logging.error("get_yield_data: Base DF fetch failed.")
        return error_return
    
    if base_df.empty:
        st.warning("Yield Pool API returned no data.")
        logging.warning("get_yield_data: Base DF is empty.")
        return warning_return

    try:
        # Filter for stablecoins and target assets
        condition_is_stablecoin_flag = base_df['stablecoin'] == True
        condition_is_target_yield_asset = base_df['join_symbol'].isin(target_yield_assets_lower)
        relevant_pools_df = base_df[condition_is_stablecoin_flag | condition_is_target_yield_asset].copy()
        
        logging.info(f"Pool Yields: Pool count after filtering for stablecoin flag or target asset: {len(relevant_pools_df)}")
        
        if relevant_pools_df.empty:
            logging.warning("get_yield_data: No relevant pools after stablecoin/target filter.")
            return warning_return

        # Apply TVL filter
        tvl_condition = relevant_pools_df['tvlUsd'].fillna(0) > min_tvl
        filtered_tvl_df = relevant_pools_df[tvl_condition].copy()
        
        logging.info(f"Pool Yields: Pool count after TVL filter (> {format_tvl(min_tvl)}): {len(filtered_tvl_df)}")
        
        if filtered_tvl_df.empty:
            logging.warning(f"get_yield_data: No relevant pools found with TVL > {format_tvl(min_tvl)}.")
            return warning_tvl_return

        # Merge with stablecoin metadata if available
        merged_df = filtered_tvl_df
        if stablecoin_metadata_df is not None and not stablecoin_metadata_df.empty:
            if 'join_symbol' not in stablecoin_metadata_df.columns and 'symbol' in stablecoin_metadata_df.columns:
                stablecoin_metadata_df['join_symbol'] = stablecoin_metadata_df['symbol'].str.lower()
                
            if 'join_symbol' in stablecoin_metadata_df.columns:
                meta_cols_to_merge = ['join_symbol', 'name', 'pegMechanism', 'pegType']
                meta_subset = stablecoin_metadata_df[
                    [col for col in meta_cols_to_merge if col in stablecoin_metadata_df.columns]
                ].drop_duplicates(subset=['join_symbol'])
                
                merged_df = pd.merge(
                    filtered_tvl_df, meta_subset, on='join_symbol', how='left', suffixes=('', '_meta')
                )
                logging.info("Pool Yields: Merged stablecoin metadata.")
            else:
                logging.warning("get_yield_data: Stablecoin metadata missing join_symbol, merge skipped.")
        else:
            logging.warning("get_yield_data: Stablecoin metadata is None or empty, merge skipped.")
            for col in ['name', 'pegMechanism', 'pegType']:
                if col not in merged_df.columns:
                    merged_df[col] = None

        # Ensure all required columns exist
        for col in ['chain', 'project', 'symbol', 'tvlUsd', 'apy', 'name', 'pegMechanism', 'pegType']:
            if col not in merged_df.columns:
                merged_df[col] = None
                
        # Rename columns for display
        rename_mapping = {
            'chain': 'Chain', 'project': 'Project', 'symbol': 'Asset Symbol',
            'apy': 'APY (%)', 'tvlUsd': 'TVL (USD)', 'name': 'Issuer/Name',
            'pegMechanism': 'Type (Peg Mechanism)', 'pegType': 'Type (Peg)'
        }
        final_df = merged_df.rename(columns=rename_mapping)

        # Store numeric values for sorting and format display values
        if 'TVL (USD)' in final_df.columns:
            final_df['TVL_Value'] = final_df['TVL (USD)']
            final_df['TVL (USD)'] = final_df['TVL (USD)'].apply(format_tvl)
        else:
            final_df['TVL_Value'] = pd.NA

        if 'APY (%)' in final_df.columns:
            final_df['apy_sort_col'] = final_df['APY (%)']
            final_df['APY (%)'] = final_df['APY (%)'].apply(format_apy)
        else:
            final_df['apy_sort_col'] = pd.NA

        # Format metadata columns in batches for better performance
        metadata_cols = ['Issuer/Name', 'Type (Peg Mechanism)', 'Type (Peg)', 'Chain', 'Project', 'Asset Symbol']
        for col in metadata_cols:
            if col in final_df.columns:
                final_df[col] = parallel_apply(final_df, format_metadata, col)

        # Sort by APY
        if 'apy_sort_col' in final_df.columns:
            final_df = final_df.sort_values(by='apy_sort_col', ascending=False, na_position='last')
            final_df = final_df.drop(columns=['apy_sort_col'])
        else:
            logging.warning("get_yield_data: Could not sort by APY, sort column missing.")

        # Select display columns
        display_columns_yield = ['Chain', 'Project', 'Asset Symbol', 'APY (%)', 'TVL (USD)', 'Issuer/Name', 'Type (Peg)']
        for col in display_columns_yield:
            if col not in final_df.columns:
                final_df[col] = "N/A"
                
        final_display_df = final_df[display_columns_yield]
        
        # Optimize memory usage
        final_display_df = optimize_dataframe(final_display_df)
        
        logging.info(f"get_yield_data: Returning {len(final_display_df)} rows for display.")
        
        return final_display_df
        
    except Exception as e:
        handle_api_error(
            e,
            "Error processing yield data",
            logging.ERROR,
            show_traceback=True
        )
        return error_return


def get_analytics_data(
    min_tvl: float,
    target_yield_assets_lower: List[str],
    stablecoin_metadata_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    Prepares data for Pool Yield Analytics (e.g., charts), keeping numeric values.
    
    Args:
        min_tvl: Minimum TVL filter value
        target_yield_assets_lower: List of target yield asset symbols in lowercase
        stablecoin_metadata_df: DataFrame with stablecoin metadata
        
    Returns:
        DataFrame with processed data for analytics
    """
    base_df = fetch_defillama_yield_pools()

    # Early return cases
    error_return = create_error_dataframe('error', "Data fetch failed")
    warning_return = create_error_dataframe('warning', "No pools matched base criteria")
    warning_tvl_return = create_error_dataframe(
        'warning_tvl', 
        f"No pools matched TVL > {format_tvl(min_tvl)}"
    )

    if base_df is None:
        logging.error("get_analytics_data: Base DF fetch failed.")
        return error_return
    
    if base_df.empty:
        st.warning("Yield Pool API returned no data for analytics.")
        logging.warning("get_analytics_data: Base DF is empty.")
        return warning_return

    try:
        # Filter for stablecoins and target assets
        condition_is_stablecoin_flag = base_df['stablecoin'] == True
        condition_is_target_yield_asset = base_df['join_symbol'].isin(target_yield_assets_lower)
        relevant_pools_df = base_df[condition_is_stablecoin_flag | condition_is_target_yield_asset].copy()
        
        logging.info(f"Pool Analytics data: Pool count after filtering for stablecoin flag or target asset: {len(relevant_pools_df)}")
        
        if relevant_pools_df.empty:
            logging.warning("get_analytics_data: No relevant pools after stablecoin/target filter.")
            return warning_return

        # Apply TVL filter
        tvl_condition = relevant_pools_df['tvlUsd'].fillna(0) > min_tvl
        filtered_tvl_df = relevant_pools_df[tvl_condition].copy()
        
        logging.info(f"Pool Analytics data: Pool count after TVL filter (> {format_tvl(min_tvl)}): {len(filtered_tvl_df)}")
        
        if filtered_tvl_df.empty:
            logging.warning(f"get_analytics_data: No relevant pools found with TVL > {format_tvl(min_tvl)}.")
            return warning_tvl_return

        # Merge with stablecoin metadata if available
        merged_df = filtered_tvl_df
        if stablecoin_metadata_df is not None and not stablecoin_metadata_df.empty:
            if 'join_symbol' not in stablecoin_metadata_df.columns and 'symbol' in stablecoin_metadata_df.columns:
                stablecoin_metadata_df['join_symbol'] = stablecoin_metadata_df['symbol'].str.lower()
                
            if 'join_symbol' in stablecoin_metadata_df.columns:
                meta_cols_to_merge = ['join_symbol', 'name', 'pegMechanism', 'pegType']
                meta_subset = stablecoin_metadata_df[
                    [col for col in meta_cols_to_merge if col in stablecoin_metadata_df.columns]
                ].drop_duplicates(subset=['join_symbol'])
                
                merged_df = pd.merge(
                    filtered_tvl_df, meta_subset, on='join_symbol', how='left', suffixes=('', '_meta')
                )
                logging.info("Pool Analytics data: Merged stablecoin metadata.")
            else:
                merged_df = filtered_tvl_df
                logging.warning("get_analytics_data: Stablecoin metadata missing join_symbol, merge skipped.")
        else:
            merged_df = filtered_tvl_df
            logging.warning("get_analytics_data: Stablecoin metadata is None or empty, merge skipped.")
            for col in ['name', 'pegMechanism', 'pegType']:
                if col not in merged_df.columns:
                    merged_df[col] = None

        # Ensure all required columns exist
        for col in ['chain', 'project', 'symbol', 'tvlUsd', 'apy', 'name', 'pegMechanism', 'pegType']:
            if col not in merged_df.columns:
                merged_df[col] = None
                
        # Rename columns for display
        rename_mapping = {
            'chain': 'Chain', 'project': 'Project', 'symbol': 'Asset Symbol',
            'apy': 'APY', 'tvlUsd': 'TVL_USD', 'name': 'Issuer/Name',
            'pegMechanism': 'Type (Peg Mechanism)', 'pegType': 'Type (Peg)'
        }
        analytics_df = merged_df.rename(columns=rename_mapping)

        # Remove rows with missing APY or TVL
        initial_rows = len(analytics_df)
        analytics_df.dropna(subset=['APY', 'TVL_USD'], inplace=True)
        dropped_rows = initial_rows - len(analytics_df)
        
        if dropped_rows > 0:
            logging.info(f"Pool Analytics data: Dropped {dropped_rows} rows with missing APY or TVL_USD.")

        # Ensure string columns have proper values
        str_cols = ['Project', 'Chain', 'Type (Peg)', 'Type (Peg Mechanism)', 'Issuer/Name', 'Asset Symbol']
        for col in str_cols:
            if col in analytics_df.columns:
                analytics_df[col] = analytics_df[col].astype(str).fillna('N/A').replace('', 'N/A')

        # Ensure all necessary columns are present
        final_analytics_columns = [
            'Chain', 'Project', 'Asset Symbol', 'APY', 'TVL_USD', 
            'Issuer/Name', 'Type (Peg)', 'Type (Peg Mechanism)'
        ]
        
        for col in final_analytics_columns:
            if col not in analytics_df.columns:
                analytics_df[col] = "N/A"

        analytics_df_final = analytics_df[final_analytics_columns]
        
        # Optimize memory usage
        analytics_df_final = optimize_dataframe(analytics_df_final)
        
        logging.info(f"get_analytics_data: Returning {len(analytics_df_final)} rows for pool analytics.")
        
        return analytics_df_final
        
    except Exception as e:
        handle_api_error(
            e,
            "Error processing analytics data",
            logging.ERROR,
            show_traceback=True
        )
        return error_return


def get_enhanced_analytics_data(manual_stablecoin_data: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    """
    Generates data for the Stablecoin Analytics plots based on manually-defined stablecoin yield data.
    Parses yield and TVL strings into numeric formats.
    
    Args:
        manual_stablecoin_data: Dictionary of manual stablecoin data
        
    Returns:
        DataFrame with processed data for stablecoin analytics
    """
    logging.info("Starting get_enhanced_analytics_data (using manual data)...")

    try:
        manual_yield_data = get_stablecoin_yields_data(manual_stablecoin_data)

        if isinstance(manual_yield_data, pd.DataFrame) and ('warning' in manual_yield_data.columns or 'error' in manual_yield_data.columns):
            logging.error("get_enhanced_analytics_data: Could not retrieve valid manual yield data.")
            return create_error_dataframe('error', "Failed to load manual source data")
            
        if manual_yield_data.empty:
            logging.warning("get_enhanced_analytics_data: Manual source data is empty.")
            return create_error_dataframe('warning', "Manual source data is empty")

        # Process the data
        analytics_df = manual_yield_data.copy()
        analytics_df.rename(columns={'Ticker': 'Asset Symbol'}, inplace=True)

        # Apply transformations in batches for better performance
        def parse_yield_batch(batch: pd.DataFrame) -> pd.DataFrame:
            batch['APY'] = batch['Yield'].apply(parse_yield)
            return batch
            
        def parse_tvl_batch(batch: pd.DataFrame) -> pd.DataFrame:
            batch['TVL_USD'] = batch['TVL'].apply(parse_tvl)
            return batch
            
        # Apply batched processing
        analytics_df = batch_process_dataframe(analytics_df, parse_yield_batch)
        analytics_df = batch_process_dataframe(analytics_df, parse_tvl_batch)

        # Categorize by strategy
        logging.info("Categorizing strategies based on manual descriptions...")
        analytics_df['Strategy Type'] = parallel_apply(
            analytics_df, 
            categorize_stablecoin_by_strategy, 
            'Description'
        )

        # Ensure all necessary columns are present
        final_columns = [
            'Project', 'Asset Symbol', 'APY', 'TVL_USD', 'Strategy Type',
            'Description', 'Staked Proportion'
        ]
        
        for col in final_columns:
            if col not in analytics_df.columns:
                analytics_df[col] = None

        enhanced_df = analytics_df[final_columns].copy()

        # Remove rows with missing APY or TVL
        initial_rows_enhanced = len(enhanced_df)
        enhanced_df.dropna(subset=['APY', 'TVL_USD'], inplace=True)
        dropped_rows_enhanced = initial_rows_enhanced - len(enhanced_df)
        
        if dropped_rows_enhanced > 0:
            logging.info(f"Enhanced Analytics (Manual): Dropped {dropped_rows_enhanced} rows with missing numeric APY or TVL_USD.")

        # Ensure string columns have proper values
        str_cols = ['Project', 'Asset Symbol', 'Description', 'Strategy Type']
        for col in str_cols:
            if col in enhanced_df.columns:
                enhanced_df[col] = enhanced_df[col].astype(str).fillna('N/A').replace('', 'N/A')

        # Optimize memory usage
        enhanced_df = optimize_dataframe(enhanced_df)

        logging.info(f"get_enhanced_analytics_data (Manual): Returning {len(enhanced_df)} final rows.")
        
        return enhanced_df
        
    except Exception as e:
        handle_api_error(
            e,
            "Error processing enhanced analytics data",
            logging.ERROR,
            show_traceback=True
        )
        return create_error_dataframe('error', "Failed to process enhanced analytics data")


@st.cache_data(ttl=3600)
def get_stablecoin_yields_data(manual_stablecoin_data: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    """
    Generates the stablecoin yield table based only on the manual stablecoin data dictionary.
    
    Args:
        manual_stablecoin_data: Dictionary of manual stablecoin data
        
    Returns:
        DataFrame with processed manual stablecoin data
    """
    logging.info("Starting get_stablecoin_yields_data (using manual data)...")

    try:
        rows = []
        for key, data in manual_stablecoin_data.items():
            rows.append({
                'Project': data.get('Project', 'N/A'),
                'Ticker': data.get('Ticker', key.upper()),
                'Yield': data.get('Yield', 'N/A'),
                'TVL': data.get('TVL', 'N/A'),
                'Description': data.get('Description', 'N/A'),
                'Staked Proportion': format_staked_proportion(data.get('StakedProportion', 'N/A')),
                'Yield_sort': parse_yield(data.get('Yield', 'N/A'))
            })

        if not rows:
            logging.warning("Manual stablecoin data is empty.")
            return create_error_dataframe('warning', "Manual stablecoin data is empty")

        result_df = pd.DataFrame(rows)

        # Sort by yield
        result_df = result_df.sort_values('Yield_sort', ascending=False, na_position='last')
        result_df = result_df.drop(columns=['Yield_sort'])

        # Clean up any NA values
        for col in result_df.columns:
            result_df[col] = result_df[col].replace(['', '?', None, np.nan], 'N/A')

        # Ensure all required columns are present
        required_cols = ['Project', 'Ticker', 'Yield', 'TVL', 'Description', 'Staked Proportion']
        for col in required_cols:
            if col not in result_df.columns:
                result_df[col] = "N/A"
                logging.warning(f"Added missing required column: {col}")

        # Optimize memory usage
        result_df = optimize_dataframe(result_df)

        logging.info(f"get_stablecoin_yields_data: Returning {len(result_df)} manual rows.")
        
        return result_df[required_cols]
        
    except Exception as e:
        handle_api_error(
            e,
            "Error processing stablecoin yields data",
            logging.ERROR,
            show_traceback=True
        )
        return create_error_dataframe('error', "Failed to process stablecoin yields data")