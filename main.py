import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
import logging 
import os 
import re 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(layout="wide")

DEFILLAMA_YIELDS_API_URL = "https://yields.llama.fi/pools"
DEFILLAMA_STABLECOINS_API_URL = "https://stablecoins.llama.fi/stablecoins"
DEFILLAMA_PROTOCOL_API_URL = "https://api.llama.fi/protocols" 
DEFAULT_MIN_TVL_USD = 10_000_000 
API_TIMEOUT = 20 
API_RETRIES = 3
API_DELAY = 5 
LOGO_PATH = "izun_partners_logo.jpeg" 

TARGET_YIELD_ASSET_SYMBOLS_LOWER = list(set([
    'susdf', 'sgyd', 'arusd', 'yusd', 'ivlusd', 'sdola', 'wusdn', 'avusd',
    'syrupusdc', 'srusd', 'usds', 'stusr', 'crt', 'bold', 'stusd', 'susda',
    'cgusd', 'smoney', 'csusdl', 'susds', 'susn', 'usdy', 'usd3', 'usdo',
    'musdm', 'sdeusd', 'susde', 'usyc', 'crvusd', 'stkgho', 'scusd', 'susdx',
    'perenausd', 'usd0',
]))

MANUAL_STABLECOIN_DATA = {
    'susdf': {'Project': '@FalconStables', 'Ticker': 'SUSDF', 'Yield': '14.40%', 'TVL': '$218M', 'Description': 'Diversified institutional trading strategies', 'StakedProportion': '78.30%'},
    'sgyd': {'Project': '@GyroStable', 'Ticker': 'SGYD', 'Yield': '10.20%', 'TVL': '$60M', 'Description': 'native protocol yield', 'StakedProportion': '1.42%'},
    'arusd': {'Project': '@protocol_fx', 'Ticker': 'ARUSD', 'Yield': '8.27%', 'TVL': '$23M', 'Description': 'restaking rewards, including points', 'StakedProportion': '?'},
    'yusd': {'Project': '@GetYieldFi', 'Ticker': 'YUSD', 'Yield': '10.24%', 'TVL': '$12.9M', 'Description': 'allocates funds across defi bluechips', 'StakedProportion': 'N/A'},
    'ivlusd': {'Project': '@levelusds', 'Ticker': 'LVLUSD', 'Yield': '9.28%', 'TVL': '$167M', 'Description': 'lending/restaking', 'StakedProportion': '34.62%'},
    'sdola': {'Project': '@InverseFinance', 'Ticker': 'SDOLA', 'Yield': '6.91%', 'TVL': '$25.5M', 'Description': 'native protocol yield', 'StakedProportion': '35.85%'},
    'wusdn': {'Project': '@SmarDex', 'Ticker': 'WUSDN', 'Yield': '17.8%', 'TVL': '$2.2M', 'Description': 'delta neutral strategy', 'StakedProportion': '?'},
    'avusd': {'Project': '@avantprotocol', 'Ticker': 'AVUSD', 'Yield': '10.26%', 'TVL': '$43.9M', 'Description': 'arb / cash & carry', 'StakedProportion': '0.00%'},
    'syrupusdc': {'Project': '@syrupfi', 'Ticker': 'SYRUPUSDC', 'Yield': '10.4%', 'TVL': '$702.2M', 'Description': 'fixed-rate, overcollateralized loans', 'StakedProportion': 'N/A'},
    'srusd': {'Project': '@reya_xyz', 'Ticker': 'SRUSD', 'Yield': '4.23%', 'TVL': '$16M', 'Description': 'powers native DEX', 'StakedProportion': '?'},
    'usds': {'Project': '@SperaxUSD', 'Ticker': 'USDS', 'Yield': '3.01%', 'TVL': '$895K', 'Description': 'collateral put to 3rd party DeFi protocols', 'StakedProportion': 'N/A'},
    'stusr': {'Project': '@ResolvLabs', 'Ticker': 'STUSR', 'Yield': '1.9%', 'TVL': '$344M', 'Description': 'delta neutral strategy', 'StakedProportion': '18.25%'},
    'crt': {'Project': '@DeFiCarrot', 'Ticker': 'CRT', 'Yield': '4.99%', 'TVL': '$14M', 'Description': 'looks like a manual funds rebalances', 'StakedProportion': '?'},
    'bold': {'Project': '@LiquityProtocol', 'Ticker': 'BOLD', 'Yield': '5.91%', 'TVL': '$24M', 'Description': 'native protocol revenues', 'StakedProportion': 'N/A'},
    'stusd': {'Project': '@AngleProtocol', 'Ticker': 'STUSD', 'Yield': '8.1%', 'TVL': '$28.1M', 'Description': 'RWAs & borrower interest yield', 'StakedProportion': 'N/A'},
    'susda': {'Project': '@avalonfinance_', 'Ticker': 'SUSDA', 'Yield': '5%', 'TVL': '$185.8M', 'Description': 'revenue generated through USDaLend', 'StakedProportion': 'N/A'},
    'cgusd': {'Project': '@CygnusFi', 'Ticker': 'CGUSD', 'Yield': '4.84%', 'TVL': '$37.6M', 'Description': 'T-bills', 'StakedProportion': 'N/A'},
    'smoney': {'Project': '@defidotmoney', 'Ticker': 'SMONEY', 'Yield': '9.84%', 'TVL': '$172K', 'Description': 'native protocol revenues', 'StakedProportion': '41.22%'},
    'csusdl': {'Project': '@OxCoinshift', 'Ticker': 'CSUSDL', 'Yield': '3.69%', 'TVL': '$70.9M', 'Description': 'USDL (by paxos) Morpho Vault + rewards', 'StakedProportion': '88.04%'},
    'susds': {'Project': '@SkyEcosystem', 'Ticker': 'SUSDS', 'Yield': '4.50%', 'TVL': '$2.48M', 'Description': 'Sky Savings Rate', 'StakedProportion': '?'},
    'susn': {'Project': '@noon_capital', 'Ticker': 'SUSN', 'Yield': '4.53%', 'TVL': '$27.6M', 'Description': 't-bills & delta neutral strats', 'StakedProportion': '45.97%'},
    'usdy': {'Project': '@OndoFinance', 'Ticker': 'USDY', 'Yield': '4.25%', 'TVL': '$585.34M', 'Description': 'T-bills', 'StakedProportion': 'N/A'},
    'usd3': {'Project': '@reserveprotocol', 'Ticker': 'USD3', 'Yield': '3.1%', 'TVL': '$5.78M', 'Description': 'Index of different holdings, lateral exposure to aave, comp, morpho', 'StakedProportion': 'N/A'},
    'usdo': {'Project': '@OpenEden_X', 'Ticker': 'USDO', 'Yield': '4.03%', 'TVL': '$149.1M', 'Description': 'T-bills', 'StakedProportion': '43.94%'},
    'musdm': {'Project': '@MountainUSD', 'Ticker': 'MUSDM', 'Yield': '3.80%', 'TVL': '$35M', 'Description': 'T-bills', 'StakedProportion': 'N/A'},
    'sdeusd': {'Project': '@elixir', 'Ticker': 'SDEUSD', 'Yield': '3.79%', 'TVL': '$177.5M', 'Description': 'mixture of treasuries and funding yield', 'StakedProportion': '72.41%'},
    'susde': {'Project': '@ethena_labs', 'Ticker': 'SUSDE', 'Yield': '4.7%', 'TVL': '$4.67B', 'Description': 'perps funding & staked eth', 'StakedProportion': '43.20%'},
    'usyc': {'Project': '@Hashnote_Labs', 'Ticker': 'USYC', 'Yield': '3.86%', 'TVL': '$664.5M', 'Description': 'T-bills', 'StakedProportion': 'N/A'},
    'crvusd': {'Project': '@curvefinance', 'Ticker': 'CRVUSD', 'Yield': '1.1%', 'TVL': '$208.8M', 'Description': 'interest paid by crUSD minters', 'StakedProportion': 'N/A'},
    'stkgho': {'Project': '@aave', 'Ticker': 'STKGHO', 'Yield': '3.65%', 'TVL': '$159M', 'Description': 'Aave Safety Module', 'StakedProportion': 'N/A'},
    'scusd': {'Project': '@Rings_Protocol', 'Ticker': 'SCUSD', 'Yield': '5.13%', 'TVL': '$110.8M', 'Description': 'farming strategies via Veda vaults', 'StakedProportion': '63.56%'},
    'susdx': {'Project': '@StablesLabs', 'Ticker': 'SUSDX', 'Yield': '4.27%', 'TVL': '$627M', 'Description': 'Delta Neutral', 'StakedProportion': 'N/A'},
    'perenausd': {'Project': '@PerenaUSD', 'Ticker': 'PERENAUSD', 'Yield': '1.25%', 'TVL': '$26.5M', 'Description': 'swap fees of native Growth Pools', 'StakedProportion': 'N/A'},
    'usd0': {'Project': '@Usualmoney', 'Ticker': 'USD0', 'Yield': '11%', 'TVL': '$651.7M', 'Description': 'max{Treasury, Option}', 'StakedProportion': 'N/A'},
}

def format_tvl(tvl):
    """Formats TVL number into a human-readable string (B, M, K)."""
    if pd.isna(tvl) or not isinstance(tvl, (int, float)) or tvl == 0:
        return "N/A"
    if abs(tvl) >= 1_000_000_000:
        return f"${tvl / 1_000_000_000:.2f}B"
    if abs(tvl) >= 1_000_000:
        return f"${tvl / 1_000_000:.2f}M"
    if abs(tvl) >= 1_000:
        return f"${tvl / 1_000:.1f}K"
    return f"${tvl:.0f}"

def format_apy(apy):
    """Formats APY number into a percentage string."""
    if pd.isna(apy) or not isinstance(apy, (int, float)):
        return "N/A"
    return f"{apy:.2f}%"

def format_metadata(value):
    """Returns 'N/A' if value is NaN, None, or empty string, otherwise returns the value."""
    return value if pd.notna(value) and value != '' else "N/A"

def format_staked_proportion(value):
    """Handles specific formatting for staked proportion, treating '?' and empty strings as N/A."""
    if pd.isna(value) or value in ['', '?']:
        return "N/A"
    if isinstance(value, (int, float)):
         return f"{value:.2f}%"
    return str(value) 

def parse_yield(yield_str):
    """Parses yield string ('X.XX%') into a float. Returns NaN on failure."""
    if not isinstance(yield_str, str) or yield_str == 'N/A':
        return np.nan
    try:
        return float(yield_str.strip().replace('%', ''))
    except (ValueError, AttributeError):
        return np.nan

def parse_tvl(tvl_str):
    """Parses TVL string ('$X.XX[B/M/K]') into a float USD value. Returns NaN on failure."""
    if not isinstance(tvl_str, str) or tvl_str == 'N/A':
        return np.nan
    try:
        tvl_str = tvl_str.strip().replace('$', '').replace(',', '').lower()
        multiplier = 1
        if tvl_str.endswith('b'):
            multiplier = 1_000_000_000
            tvl_str = tvl_str[:-1]
        elif tvl_str.endswith('m'):
            multiplier = 1_000_000
            tvl_str = tvl_str[:-1]
        elif tvl_str.endswith('k'):
            multiplier = 1_000
            tvl_str = tvl_str[:-1]

        return float(tvl_str) * multiplier
    except (ValueError, AttributeError):
        return np.nan

@st.cache_data(ttl=1800) 
def get_stablecoin_metadata(retries=API_RETRIES, delay=API_DELAY):
    """Fetches stablecoin metadata from DefiLlama (Used for Pool Yields filters)."""
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(DEFILLAMA_STABLECOINS_API_URL, timeout=API_TIMEOUT)
            response.raise_for_status() 
            data = response.json()

            if 'peggedAssets' not in data or not isinstance(data['peggedAssets'], list):
                st.error("Unexpected Stablecoin Metadata API response format.")
                logging.error("Stablecoin Metadata API response format error: %s", data)
                return pd.DataFrame() 

            meta_df = pd.DataFrame(data['peggedAssets'])
            cols_to_keep = ['symbol', 'name', 'pegMechanism', 'pegType']
            meta_df = meta_df[[col for col in cols_to_keep if col in meta_df.columns]].copy()
            meta_df['join_symbol'] = meta_df['symbol'].str.lower() 
            return meta_df

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            attempt += 1
            msg = f"Stablecoin Metadata API request failed (Attempt {attempt}/{retries}): {e}"
            logging.warning(msg)
            if attempt < retries:
                st.warning(f"{msg}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                st.error(f"Failed to fetch Stablecoin Metadata after {retries} attempts.")
                logging.error("Final attempt failed for Stablecoin Metadata API.")
                return pd.DataFrame()
    return pd.DataFrame()

@st.cache_data(ttl=600) 
def _fetch_defillama_yield_pools(retries=API_RETRIES, delay=API_DELAY):
    """Internal function to fetch and perform initial processing of yield pool data (Used for Pool Yields)."""
    attempt = 0
    while attempt < retries:
        try:
            logging.info("Fetching yield pool data from DefiLlama...")
            response = requests.get(DEFILLAMA_YIELDS_API_URL, timeout=API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            logging.info("Successfully fetched yield pool data.")

            if 'data' not in data or not isinstance(data['data'], list):
                st.error("Unexpected Yield Pool API response format.")
                logging.error("Yield Pool API response format error: %s", data)
                return None 

            df = pd.DataFrame(data['data'])
            logging.info(f"Initial pool count: {len(df)}")

            if 'stablecoin' not in df.columns: df['stablecoin'] = False
            if 'symbol' not in df.columns: df['symbol'] = ''
            if 'tvlUsd' not in df.columns: df['tvlUsd'] = pd.NA
            if 'apy' not in df.columns: df['apy'] = pd.NA
            if 'project' not in df.columns: df['project'] = 'Unknown'
            if 'chain' not in df.columns: df['chain'] = 'Unknown'

            df['stablecoin'] = pd.to_numeric(df['stablecoin'], errors='coerce').fillna(0).astype(bool)
            df['symbol'] = df['symbol'].astype(str)
            df['project'] = df['project'].astype(str)
            df['chain'] = df['chain'].astype(str)
            df['tvlUsd'] = pd.to_numeric(df['tvlUsd'], errors='coerce')
            df['apy'] = pd.to_numeric(df['apy'], errors='coerce')
            df['join_symbol'] = df['symbol'].str.lower()

            return df

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            attempt += 1
            msg = f"Yield Pool API request failed (Attempt {attempt}/{retries}): {e}"
            logging.warning(msg)
            if attempt < retries:
                st.warning(f"{msg}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                st.error(f"Failed to fetch Yield Pool data after {retries} attempts.")
                logging.error("Final attempt failed for Yield Pool API.")
                return None 
    return None

def get_yield_data(min_tvl, target_yield_assets_lower, stablecoin_metadata_df):
    """
    Processes yield pool data FOR THE POOL YIELDS TABLE, filtering, merging metadata, and formatting.
    Relies on _fetch_defillama_yield_pools for the base data.
    """
    base_df = _fetch_defillama_yield_pools()

    error_return = pd.DataFrame({'error': ["Data fetch failed"]})
    warning_return = pd.DataFrame({'warning': ["No pools matched base criteria"]})
    warning_tvl_return = pd.DataFrame({'warning_tvl': [f"No pools matched TVL > {format_tvl(min_tvl)}"]})

    if base_df is None:
        logging.error("get_yield_data: Base DF fetch failed.")
        return error_return
    if base_df.empty:
        st.warning("Yield Pool API returned no data.")
        logging.warning("get_yield_data: Base DF is empty.")
        return warning_return

    condition_is_stablecoin_flag = base_df['stablecoin'] == True
    condition_is_target_yield_asset = base_df['join_symbol'].isin(target_yield_assets_lower)
    relevant_pools_df = base_df[condition_is_stablecoin_flag | condition_is_target_yield_asset].copy()
    logging.info(f"Pool Yields: Pool count after filtering for stablecoin flag or target asset: {len(relevant_pools_df)}")
    if relevant_pools_df.empty:
        logging.warning("get_yield_data: No relevant pools after stablecoin/target filter.")
        return warning_return

    tvl_condition = relevant_pools_df['tvlUsd'].fillna(0) > min_tvl
    filtered_tvl_df = relevant_pools_df[tvl_condition].copy()
    logging.info(f"Pool Yields: Pool count after TVL filter (> {format_tvl(min_tvl)}): {len(filtered_tvl_df)}")
    if filtered_tvl_df.empty:
        logging.warning(f"get_yield_data: No relevant pools found with TVL > {format_tvl(min_tvl)}.")
        return warning_tvl_return

    merged_df = filtered_tvl_df
    if stablecoin_metadata_df is not None and not stablecoin_metadata_df.empty:
        if 'join_symbol' not in stablecoin_metadata_df.columns and 'symbol' in stablecoin_metadata_df.columns:
            stablecoin_metadata_df['join_symbol'] = stablecoin_metadata_df['symbol'].str.lower()
        if 'join_symbol' in stablecoin_metadata_df.columns:
             meta_cols_to_merge = ['join_symbol', 'name', 'pegMechanism', 'pegType']
             meta_subset = stablecoin_metadata_df[[col for col in meta_cols_to_merge if col in stablecoin_metadata_df.columns]].drop_duplicates(subset=['join_symbol'])
             merged_df = pd.merge(filtered_tvl_df, meta_subset, on='join_symbol', how='left', suffixes=('', '_meta'))
             logging.info("Pool Yields: Merged stablecoin metadata.")
        else:
             logging.warning("get_yield_data: Stablecoin metadata missing join_symbol, merge skipped.")
    else:
        logging.warning("get_yield_data: Stablecoin metadata is None or empty, merge skipped.")
        if 'name' not in merged_df.columns: merged_df['name'] = None
        if 'pegMechanism' not in merged_df.columns: merged_df['pegMechanism'] = None
        if 'pegType' not in merged_df.columns: merged_df['pegType'] = None

    for col in ['chain', 'project', 'symbol', 'tvlUsd', 'apy', 'name', 'pegMechanism', 'pegType']:
        if col not in merged_df.columns: merged_df[col] = None
    rename_mapping = {
        'chain': 'Chain', 'project': 'Project', 'symbol': 'Asset Symbol',
        'apy': 'APY (%)', 'tvlUsd': 'TVL (USD)', 'name': 'Issuer/Name',
        'pegMechanism': 'Type (Peg Mechanism)', 'pegType': 'Type (Peg)'
    }
    final_df = merged_df.rename(columns=rename_mapping)

    if 'TVL (USD)' in final_df.columns:
        final_df['TVL_Value'] = final_df['TVL (USD)']
        final_df['TVL (USD)'] = final_df['TVL (USD)'].apply(format_tvl)
    else: final_df['TVL_Value'] = pd.NA

    if 'APY (%)' in final_df.columns:
        final_df['apy_sort_col'] = final_df['APY (%)']
        final_df['APY (%)'] = final_df['APY (%)'].apply(format_apy)
    else: final_df['apy_sort_col'] = pd.NA

    for col in ['Issuer/Name', 'Type (Peg Mechanism)', 'Type (Peg)', 'Chain', 'Project', 'Asset Symbol']:
        if col in final_df.columns: final_df[col] = final_df[col].apply(format_metadata)

    if 'apy_sort_col' in final_df.columns:
        final_df = final_df.sort_values(by='apy_sort_col', ascending=False, na_position='last').drop(columns=['apy_sort_col'])
    else: logging.warning("get_yield_data: Could not sort by APY, sort column missing.")

    display_columns_yield = ['Chain', 'Project', 'Asset Symbol', 'APY (%)', 'TVL (USD)', 'Issuer/Name', 'Type (Peg)']
    for col in display_columns_yield:
        if col not in final_df.columns: final_df[col] = "N/A"
    final_display_df = final_df[display_columns_yield]
    logging.info(f"get_yield_data: Returning {len(final_display_df)} rows for display.")
    return final_display_df

def get_analytics_data(min_tvl, target_yield_assets_lower, stablecoin_metadata_df):
    """
    Prepares data FOR POOL YIELD ANALYTICS (e.g., charts), keeping numeric values.
    Relies on _fetch_defillama_yield_pools for the base data.
    """
    base_df = _fetch_defillama_yield_pools()

    error_return = pd.DataFrame({'error': ["Data fetch failed"]})
    warning_return = pd.DataFrame({'warning': ["No pools matched base criteria"]})
    warning_tvl_return = pd.DataFrame({'warning_tvl': [f"No pools matched TVL > {format_tvl(min_tvl)}"]})

    if base_df is None:
        logging.error("get_analytics_data: Base DF fetch failed.")
        return error_return
    if base_df.empty:
        st.warning("Yield Pool API returned no data for analytics.")
        logging.warning("get_analytics_data: Base DF is empty.")
        return warning_return

    condition_is_stablecoin_flag = base_df['stablecoin'] == True
    condition_is_target_yield_asset = base_df['join_symbol'].isin(target_yield_assets_lower)
    relevant_pools_df = base_df[condition_is_stablecoin_flag | condition_is_target_yield_asset].copy()
    logging.info(f"Pool Analytics data: Pool count after filtering for stablecoin flag or target asset: {len(relevant_pools_df)}")
    if relevant_pools_df.empty:
         logging.warning("get_analytics_data: No relevant pools after stablecoin/target filter.")
         return warning_return

    tvl_condition = relevant_pools_df['tvlUsd'].fillna(0) > min_tvl
    filtered_tvl_df = relevant_pools_df[tvl_condition].copy()
    logging.info(f"Pool Analytics data: Pool count after TVL filter (> {format_tvl(min_tvl)}): {len(filtered_tvl_df)}")
    if filtered_tvl_df.empty:
        logging.warning(f"get_analytics_data: No relevant pools found with TVL > {format_tvl(min_tvl)}.")
        return warning_tvl_return

    merged_df = filtered_tvl_df
    if stablecoin_metadata_df is not None and not stablecoin_metadata_df.empty:
        if 'join_symbol' not in stablecoin_metadata_df.columns and 'symbol' in stablecoin_metadata_df.columns:
            stablecoin_metadata_df['join_symbol'] = stablecoin_metadata_df['symbol'].str.lower()
        if 'join_symbol' in stablecoin_metadata_df.columns:
             meta_cols_to_merge = ['join_symbol', 'name', 'pegMechanism', 'pegType']
             meta_subset = stablecoin_metadata_df[[col for col in meta_cols_to_merge if col in stablecoin_metadata_df.columns]].drop_duplicates(subset=['join_symbol'])
             merged_df = pd.merge(filtered_tvl_df, meta_subset, on='join_symbol', how='left', suffixes=('', '_meta'))
             logging.info("Pool Analytics data: Merged stablecoin metadata.")
        else:
             merged_df = filtered_tvl_df
             logging.warning("get_analytics_data: Stablecoin metadata missing join_symbol, merge skipped.")
    else:
        merged_df = filtered_tvl_df
        logging.warning("get_analytics_data: Stablecoin metadata is None or empty, merge skipped.")
        if 'name' not in merged_df.columns: merged_df['name'] = None
        if 'pegMechanism' not in merged_df.columns: merged_df['pegMechanism'] = None
        if 'pegType' not in merged_df.columns: merged_df['pegType'] = None

    for col in ['chain', 'project', 'symbol', 'tvlUsd', 'apy', 'name', 'pegMechanism', 'pegType']:
         if col not in merged_df.columns: merged_df[col] = None
    rename_mapping = {
        'chain': 'Chain', 'project': 'Project', 'symbol': 'Asset Symbol',
        'apy': 'APY', 'tvlUsd': 'TVL_USD', 'name': 'Issuer/Name',
        'pegMechanism': 'Type (Peg Mechanism)', 'pegType': 'Type (Peg)'
    }
    analytics_df = merged_df.rename(columns=rename_mapping)

    initial_rows = len(analytics_df)
    analytics_df.dropna(subset=['APY', 'TVL_USD'], inplace=True)
    dropped_rows = initial_rows - len(analytics_df)
    if dropped_rows > 0: logging.info(f"Pool Analytics data: Dropped {dropped_rows} rows with missing APY or TVL_USD.")

    for col in ['Project', 'Chain', 'Type (Peg)', 'Type (Peg Mechanism)', 'Issuer/Name', 'Asset Symbol']:
         if col in analytics_df.columns: analytics_df[col] = analytics_df[col].astype(str).fillna('N/A').replace('', 'N/A')

    final_analytics_columns = ['Chain', 'Project', 'Asset Symbol', 'APY', 'TVL_USD', 'Issuer/Name', 'Type (Peg)', 'Type (Peg Mechanism)']
    for col in final_analytics_columns:
        if col not in analytics_df.columns: analytics_df[col] = "N/A"

    analytics_df_final = analytics_df[final_analytics_columns]
    logging.info(f"get_analytics_data: Returning {len(analytics_df_final)} rows for pool analytics.")
    return analytics_df_final

@st.cache_data(ttl=3600) 
def get_stablecoin_yields_data():
    """
    Generates the stablecoin yield table based *only* on the MANUAL_STABLECOIN_DATA dictionary.
    No API calls are made in this function.
    """
    logging.info("Starting get_stablecoin_yields_data (using manual data)...")

    rows = []
    for key, data in MANUAL_STABLECOIN_DATA.items():
        rows.append({
            'Project': data.get('Project', 'N/A'),
            'Ticker': data.get('Ticker', key.upper()),
            'Yield': data.get('Yield', 'N/A'),
            'TVL': data.get('TVL', 'N/A'),
            'Description': data.get('Description', 'N/A'),
            'Staked Proportion': format_staked_proportion(data.get('Staked Proportion', 'N/A')),
            'Yield_sort': parse_yield(data.get('Yield', 'N/A'))
        })

    if not rows:
        logging.warning("MANUAL_STABLECOIN_DATA is empty.")
        return pd.DataFrame({'warning': ["Manual stablecoin data is empty"]})

    result_df = pd.DataFrame(rows)

    result_df = result_df.sort_values('Yield_sort', ascending=False, na_position='last').drop(columns=['Yield_sort'])

    for col in result_df.columns:
        result_df[col] = result_df[col].replace(['', '?', None, np.nan], 'N/A')

    required_cols = ['Project', 'Ticker', 'Yield', 'TVL', 'Description', 'Staked Proportion']
    for col in required_cols:
        if col not in result_df.columns:
            result_df[col] = "N/A"
            logging.warning(f"Added missing required column: {col}")

    logging.info(f"get_stablecoin_yields_data: Returning {len(result_df)} manual rows.")
    return result_df[required_cols] 

def get_enhanced_analytics_data():
    """
    Generates data for the Stablecoin Analytics plots based *only* on the manually-defined
    stablecoin yield data. Parses yield and TVL strings into numeric formats.
    """
    logging.info("Starting get_enhanced_analytics_data (using manual data)...")

    manual_yield_data = get_stablecoin_yields_data()

    if 'warning' in manual_yield_data.columns or 'error' in manual_yield_data.columns:
         logging.error("get_enhanced_analytics_data: Could not retrieve valid manual yield data.")
         return pd.DataFrame({'error': ["Failed to load manual source data"]})
    if manual_yield_data.empty:
        logging.warning("get_enhanced_analytics_data: Manual source data is empty.")
        return pd.DataFrame({'warning': ["Manual source data is empty"]})


    analytics_df = manual_yield_data.copy()
    analytics_df.rename(columns={'Ticker': 'Asset Symbol'}, inplace=True) 

    analytics_df['APY'] = analytics_df['Yield'].apply(parse_yield)
    analytics_df['TVL_USD'] = analytics_df['TVL'].apply(parse_tvl)

    logging.info("Categorizing strategies based on manual descriptions...")
    def categorize_stablecoin(desc):
        desc = str(desc).lower()
        if pd.isna(desc) or desc == 'n/a' or desc == '': return 'Unknown/Other'
        if 't-bill' in desc or 'treasury' in desc or 'rwa' in desc: return 'RWA/Treasury-backed'
        if 'delta neutral' in desc or 'funding' in desc or 'cash & carry' in desc or 'delta neutra' in desc or 'perps funding' in desc: return 'Delta Neutral/Arb'
        if 'restaking' in desc: return 'Restaking'
        if 'native protocol yield' in desc or 'protocol revenue' in desc or 'interest paid by' in desc or 'safety module' in desc or 'native dex' in desc or 'sky savings rate' in desc: return 'Protocol Native Yield'
        if 'loan' in desc or 'lend' in desc or 'borrower interest' in desc or 'morpho vault' in desc: return 'Lending/Borrowing'
        if 'index' in desc or 'diversified' in desc or 'mixture' in desc: return 'Index/Diversified'
        if 'farming' in desc or '3rd party defi' in desc or 'across defi bluechips' in desc: return 'External DeFi Farming'
        if 'institutional trading' in desc: return 'Trading Strategy'
        if 'swap fees' in desc : return 'LP Fees'
        if 'option' in desc : return 'Options/Structured Product'
        return 'Unknown/Other'

    analytics_df['Strategy Type'] = analytics_df['Description'].apply(categorize_stablecoin)
    logging.info("Finished categorizing strategies.")

    final_columns = [
        'Project', 'Asset Symbol', 'APY', 'TVL_USD', 'Strategy Type',
        'Description', 'Staked Proportion'
    ]
    for col in final_columns:
        if col not in analytics_df.columns:
             analytics_df[col] = None 

    enhanced_df = analytics_df[final_columns].copy()


    initial_rows_enhanced = len(enhanced_df)
    enhanced_df.dropna(subset=['APY', 'TVL_USD'], inplace=True)
    dropped_rows_enhanced = initial_rows_enhanced - len(enhanced_df)
    if dropped_rows_enhanced > 0:
        logging.info(f"Enhanced Analytics (Manual): Dropped {dropped_rows_enhanced} rows with missing numeric APY or TVL_USD.")


    for col in ['Project', 'Asset Symbol', 'Description', 'Strategy Type']:
        if col in enhanced_df.columns:
            enhanced_df[col] = enhanced_df[col].astype(str).fillna('N/A').replace('', 'N/A')


    logging.info(f"get_enhanced_analytics_data (Manual): Returning {len(enhanced_df)} final rows.")
    return enhanced_df

with st.sidebar:
    if os.path.exists(LOGO_PATH):
        try:
            st.image(LOGO_PATH)
        except Exception as e:
            st.warning(f"Could not display logo image: {e}")
            logging.warning(f"Failed to display logo: {e}")
    else:
        st.warning(f"Logo file '{LOGO_PATH}' not found.")
        logging.warning(f"Logo file not found at: {LOGO_PATH}")

    st.title("Izun Dashboard")

    navigation_options = [
        "Overview",
        "Stablecoin Yields",       
        "Stablecoin Analytics",    
        "Pool Yields",             
        "Pool Yield Analytics",    
    ]
    choice = st.radio("Navigation", navigation_options, key="nav_choice")
    st.info("team@izun.io")

try:
    london_time = pd.Timestamp.now(tz='Europe/London')
    refresh_time_str = london_time.strftime('%Y-%m-%d %H:%M:%S %Z')
except Exception:
    refresh_time_str = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')


if choice == "Overview":
    st.title('Izun - Dashboard')
    st.markdown(f"""

        * **Stablecoin Yields**: Table of yield-bearing stablecoins.
        * **Stablecoin Analytics**: Analytics from the data in the 'Stablecoin Yields' section.
        * **Pool Yields**: Table showing yields for all asset pools on DefiLlama.
        * **Pool Yield Analytics**: Analytics dashboard on the asset pool market.

        **Link to external stablecoin dashboards:**

        * Artemis: [https://app.artemisanalytics.com/stablecoins](https://app.artemisanalytics.com/stablecoins)
        * Stablecoin.wtf: [https://stablecoins.wtf/](https://stablecoins.wtf/)
        * Footprint: [https://www.footprint.network/@DamonSalvatore/Stablecoin-Dashboard?channel=ENG-260](https://www.footprint.network/@DamonSalvatore/Stablecoin-Dashboard?channel=ENG-260)
        * Orbital: [https://www.getorbital.com/stablecoin-dashboard](https://www.getorbital.com/stablecoin-dashboard)
        * Defi Llama: [https://defillama.com/stablecoins](https://defillama.com/stablecoins)
        * RWA.xyz: [https://app.rwa.xyz/stablecoins](https://app.rwa.xyz/stablecoins)
        * IntoTheBlock: [https://app.intotheblock.com/perspectives/stablecoins](https://app.intotheblock.com/perspectives/stablecoins)
    """)


if choice == "Stablecoin Yields":
    st.title("Stablecoin Yields")
    st.caption(f"Data manually updated on a weekly basis")

    stablecoin_yield_data = get_stablecoin_yields_data()

    data_valid = not (isinstance(stablecoin_yield_data, pd.DataFrame) and
                        ('error' in stablecoin_yield_data.columns or 'warning' in stablecoin_yield_data.columns))

    filtered_data = pd.DataFrame()
    options_projects = ["All"]
    options_strategy = ["All"] 

    if data_valid and not stablecoin_yield_data.empty:
        filtered_data = stablecoin_yield_data.copy()

        def categorize_stablecoin_filter(desc): 
            desc = str(desc).lower()
            if pd.isna(desc) or desc == 'n/a' or desc == '': return 'Unknown/Other'
            if 't-bill' in desc or 'treasury' in desc or 'rwa' in desc: return 'RWA/Treasury-backed'
            if 'delta neutral' in desc or 'funding' in desc or 'cash & carry' in desc or 'delta neutra' in desc or 'perps funding' in desc: return 'Delta Neutral/Arb'
            if 'restaking' in desc: return 'Restaking'
            if 'native protocol yield' in desc or 'protocol revenue' in desc or 'interest paid by' in desc or 'safety module' in desc or 'native dex' in desc or 'sky savings rate' in desc: return 'Protocol Native Yield'
            if 'loan' in desc or 'lend' in desc or 'borrower interest' in desc or 'morpho vault' in desc: return 'Lending/Borrowing'
            if 'index' in desc or 'diversified' in desc or 'mixture' in desc: return 'Index/Diversified'
            if 'farming' in desc or '3rd party defi' in desc or 'across defi bluechips' in desc: return 'External DeFi Farming'
            if 'institutional trading' in desc: return 'Trading Strategy'
            if 'swap fees' in desc : return 'LP Fees'
            if 'option' in desc : return 'Options/Structured Product'
            return 'Unknown/Other'
        filtered_data['Strategy Type'] = filtered_data['Description'].apply(categorize_stablecoin_filter)

        if 'Project' in filtered_data.columns:
            options_projects.extend(sorted(filtered_data['Project'].dropna().unique()))
        if 'Strategy Type' in filtered_data.columns:
            options_strategy.extend(sorted(filtered_data['Strategy Type'].dropna().unique()))

        st.subheader("Filters")
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_ticker = st.text_input("Filter by Ticker Contains", placeholder="e.g. susde", key="stable_yields_ticker_filter")
        with col2:
            filter_project = st.selectbox("Filter by Project", options=options_projects, index=0, key="stable_yields_project_filter")
        with col3:
            filter_strategy = st.selectbox("Filter by Strategy Type", options=options_strategy, index=0, key="stable_yields_strategy_filter")

        if filter_ticker:
            if 'Ticker' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['Ticker'].str.lower().str.contains(filter_ticker.lower())]
            else: st.error("Filtering failed: 'Ticker' column not found.")

        if filter_project != "All":
            if 'Project' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['Project'] == filter_project]
            else: st.warning("Cannot filter by project: 'Project' column missing.")

        if filter_strategy != "All":
             if 'Strategy Type' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['Strategy Type'] == filter_strategy]
             else: st.warning("Cannot filter by strategy: 'Strategy Type' column missing.")

        


    elif isinstance(stablecoin_yield_data, pd.DataFrame) and 'error' in stablecoin_yield_data.columns:
         st.error(f"Failed to load stablecoin yield data: {stablecoin_yield_data['error'].iloc[0]}")
    elif isinstance(stablecoin_yield_data, pd.DataFrame) and 'warning' in stablecoin_yield_data.columns:
         st.warning(f"Could not load all stablecoin yield data: {stablecoin_yield_data['warning'].iloc[0]}")
    elif stablecoin_yield_data.empty:
        st.warning("No data loaded for stablecoin yields (Manual data might be empty).")


    st.divider()

    if not filtered_data.empty and data_valid:
        st.info(f"Displaying {len(filtered_data)} target stablecoins.")

        display_cols = ['Project', 'Ticker', 'Yield', 'TVL', 'Description']
        

        cols_to_display = [col for col in display_cols if col in filtered_data.columns]


        column_config = {
            "Project": st.column_config.TextColumn("Project", help="Associated project/protocol (manual)"),
            "Ticker": st.column_config.TextColumn("Ticker", help="Yield-bearing asset symbol (manual)"),
            "Yield": st.column_config.TextColumn("Yield", help="Manually entered APY (%)"),
            "TVL": st.column_config.TextColumn("TVL", help="Manually entered TVL (USD)"),
            "Description": st.column_config.TextColumn("Description", help="Yield source description (manual)"),
            "Staked Proportion": st.column_config.TextColumn("Staked %", help="Staked proportion (manual)"),
            
        }

        column_config_filtered = {k: v for k, v in column_config.items() if k in cols_to_display}

        st.dataframe(filtered_data[cols_to_display], column_config=column_config_filtered, hide_index=True, use_container_width=True)

    elif filtered_data.empty and (filter_ticker or filter_project != "All" or filter_strategy != "All") and data_valid:
        st.warning("No stablecoin yields match the selected filter criteria.")
    elif filtered_data.empty and not data_valid:
         pass 
    elif filtered_data.empty:
         st.warning("No data available for stablecoin yields overview.")


if choice == "Stablecoin Analytics":
    st.title("Stablecoin Analytics")
    st.caption(f"Analytics derived from data in 'Stablecoin Yields' section.")

    enhanced_analytics_data = get_enhanced_analytics_data()

    data_valid = not (isinstance(enhanced_analytics_data, pd.DataFrame) and
                        any(col in enhanced_analytics_data.columns for col in ['error', 'warning']))

    if data_valid and not enhanced_analytics_data.empty:

        st.subheader("Top Stablecoins by Yield")
        try:
            if 'APY' in enhanced_analytics_data.columns and 'Asset Symbol' in enhanced_analytics_data.columns:
                top_n_yield = min(20, len(enhanced_analytics_data)) 
                top_yield_enhanced = enhanced_analytics_data.nlargest(top_n_yield, 'APY')
                if not top_yield_enhanced.empty:
                    color_col = 'Strategy Type' if 'Strategy Type' in top_yield_enhanced.columns else None
                    hover_cols = ['Project', 'TVL_USD', 'Staked Proportion', 'Description'] 
                    hover_cols_exist = [col for col in hover_cols if col in top_yield_enhanced.columns]

                    fig_top_yield = px.bar(
                        top_yield_enhanced.sort_values('APY', ascending=True),
                        x='APY', y='Asset Symbol', orientation='h',
                        title=f"Top {top_n_yield} Stablecoins by Yield",
                        labels={'APY': 'Annual Percentage Yield (%)', 'Asset Symbol': 'Asset Symbol'},
                        text='APY', color=color_col, hover_data=hover_cols_exist
                    )
                    fig_top_yield.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                    fig_top_yield.update_layout(
                        yaxis_title="Asset Symbol", xaxis_title="Annual Percentage Yield (%)",
                        uniformtext_minsize=8, uniformtext_mode='hide',
                        legend_title_text='Strategy Type' if color_col else None
                    )
                    st.plotly_chart(fig_top_yield, use_container_width=True)
                else: st.warning("Not enough data to display top stablecoins by yield.")
            else: st.warning("Required columns (APY, Asset Symbol) not found for Top Yield plot.")
        except Exception as e:
             st.warning(f"Could not generate Top Yield plot: {e}")
             logging.error(f"Error in Top Yield plot: {e}")

        st.divider()
        st.subheader("Distribution by Strategy Type")
        try:
            if 'Strategy Type' in enhanced_analytics_data.columns:
                strategy_counts = enhanced_analytics_data['Strategy Type'].value_counts().reset_index()
                strategy_counts.columns = ['Strategy Type', 'Count']
                if not strategy_counts.empty:
                    fig_strategy_pie = px.pie(
                        strategy_counts, values='Count', names='Strategy Type',
                        title="Distribution by Strategy Type", hole=0.4
                    )
                    fig_strategy_pie.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_strategy_pie, use_container_width=True)
                else: st.warning("No strategy type data available.")
            else: st.warning("Strategy Type information not available for distribution plot.")
        except Exception as e:
             st.warning(f"Could not generate Strategy Distribution plot: {e}")
             logging.error(f"Error in Strategy Distribution plot: {e}")

        st.divider()
        st.subheader("Average Yield by Strategy Type")
        try:
            if 'Strategy Type' in enhanced_analytics_data.columns and 'APY' in enhanced_analytics_data.columns:
                strategy_avg_yield = enhanced_analytics_data.groupby('Strategy Type')['APY'].mean().reset_index()
                strategy_avg_yield = strategy_avg_yield.sort_values('APY', ascending=False)

                if not strategy_avg_yield.empty:
                    fig_strategy_yield = px.bar(
                        strategy_avg_yield, x='Strategy Type', y='APY',
                        title="Average Yield by Strategy Type",
                        labels={'APY': 'Average Annual Percentage Yield (%)', 'Strategy Type': 'Strategy Type'},
                        text='APY', color='Strategy Type'
                    )
                    fig_strategy_yield.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                    fig_strategy_yield.update_layout(xaxis={'categoryorder':'total descending'})
                    st.plotly_chart(fig_strategy_yield, use_container_width=True)
                else: st.warning("Not enough data to display average yield by strategy type.")
            else: st.warning("Strategy Type or APY information not available for average yield plot.")
        except Exception as e:
             st.warning(f"Could not generate Average Yield plot: {e}")
             logging.error(f"Error in Average Yield plot: {e}")

        st.divider(); st.subheader("TVL vs. APY")
        try:
            if 'TVL_USD' in enhanced_analytics_data.columns and 'APY' in enhanced_analytics_data.columns and 'Project' in enhanced_analytics_data.columns and 'Asset Symbol' in enhanced_analytics_data.columns:
                if not enhanced_analytics_data.empty:
                    hover_cols = ['Strategy Type', 'Description', 'Staked Proportion']
                    hover_cols_exist = [col for col in hover_cols if col in enhanced_analytics_data.columns]
                    color_col = 'Strategy Type' if 'Strategy Type' in enhanced_analytics_data.columns else None

                    fig_scatter_tvl_apy = px.scatter(
                        enhanced_analytics_data, x="TVL_USD", y="APY",
                        color=color_col, size="TVL_USD",
                        hover_name="Asset Symbol", hover_data=hover_cols_exist,
                        log_x=True, title="TVL vs. APY (Log Scale TVL)",
                        labels={'TVL_USD': 'Total Value Locked (USD - Log Scale)', 'APY': 'Annual Percentage Yield (%)'}
                    )
                    fig_scatter_tvl_apy.update_layout(legend_title_text='Strategy Type' if color_col else "Project")
                    st.plotly_chart(fig_scatter_tvl_apy, use_container_width=True)
                else: st.warning("Not enough data points to display TVL vs APY scatter plot.")
            else: st.warning("Required columns (TVL_USD, APY, Project, Asset Symbol) not found for scatter plot.")
        except Exception as e:
             st.warning(f"Could not generate TVL vs APY plot: {e}")
             logging.error(f"Error in Stablecoin Analytics TVL vs APY plot: {e}")


    elif isinstance(enhanced_analytics_data, pd.DataFrame) and 'error' in enhanced_analytics_data.columns:
        st.error(f"Stablecoin Analytics: Failed to process data - {enhanced_analytics_data['error'].iloc[0]}")
    elif isinstance(enhanced_analytics_data, pd.DataFrame) and 'warning' in enhanced_analytics_data.columns:
         st.warning(f"Stablecoin Analytics: {enhanced_analytics_data['warning'].iloc[0]}")
         st.warning("Analytics may be incomplete.")
    else: 
        st.warning("No data available to generate stablecoin analytics plots (Data might be empty or filtered out).")


if choice == "Pool Yields":
    st.title('Pool Yields')
    st.caption(f"Data sourced from DeFiLlama | Last Refreshed: {refresh_time_str}")

    stablecoin_metadata = get_stablecoin_metadata()

    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns([1, 1.5, 1.5, 1.5])
    with col1:
        min_tvl_input = st.number_input(
            label="Minimum Pool TVL (USD)", min_value=0, max_value=10_000_000_000,
            value=DEFAULT_MIN_TVL_USD, step=1_000_000,
            help="Filter pools by minimum Total Value Locked in USD.", format="%d", key="pool_tvl_filter"
        )

    initial_yield_data = get_yield_data(min_tvl_input, TARGET_YIELD_ASSET_SYMBOLS_LOWER, stablecoin_metadata)

    selected_projects = []
    selected_types = []
    options_projects = ["All"]
    options_types = ["All"]
    filter_symbol_search = ""

    data_valid = not (isinstance(initial_yield_data, pd.DataFrame) and
                        any(col in initial_yield_data.columns for col in ['error', 'warning', 'warning_tvl']))

    if data_valid and not initial_yield_data.empty:
        try:
            if 'Project' in initial_yield_data.columns: options_projects.extend(sorted(initial_yield_data['Project'].dropna().unique()))
            if 'Type (Peg)' in initial_yield_data.columns: options_types.extend(sorted(initial_yield_data['Type (Peg)'].dropna().unique()))
        except KeyError as e:
            st.error(f"Pool Yields: Expected column missing for filter options: {e}")
            data_valid = False
        except Exception as e:
             st.error(f"Pool Yields: Error preparing filter options: {e}")
             data_valid = False

    with col2: filter_symbol_search = st.text_input("Filter Symbol Contains", placeholder="e.g. usdc, usde", disabled=not data_valid, key="pool_symbol_filter")
    with col3:
        selected_project_filter = st.selectbox("Filter by Project", options=options_projects, index=0, disabled=not data_valid, key="pool_project_filter")
        selected_projects = [] if selected_project_filter == "All" else [selected_project_filter]
    with col4:
        selected_type_filter = st.selectbox("Filter by Type (Peg)", options=options_types, index=0, disabled=not data_valid, key="pool_type_filter")
        selected_types = [] if selected_type_filter == "All" else [selected_type_filter]

    filtered_yield_data = pd.DataFrame()
    if data_valid and not initial_yield_data.empty:
        filtered_yield_data = initial_yield_data.copy()
        try:
            if filter_symbol_search:
                if 'Asset Symbol' in filtered_yield_data.columns: filtered_yield_data = filtered_yield_data[filtered_yield_data['Asset Symbol'].str.lower().str.contains(filter_symbol_search.lower())]
                else: st.warning("Pool Yields: Cannot filter by symbol: 'Asset Symbol' column missing.")
            if selected_projects:
                 if 'Project' in filtered_yield_data.columns: filtered_yield_data = filtered_yield_data[filtered_yield_data['Project'].isin(selected_projects)]
                 else: st.warning("Pool Yields: Cannot filter by project: 'Project' column missing.")
            if selected_types:
                if 'Type (Peg)' in filtered_yield_data.columns: filtered_yield_data = filtered_yield_data[filtered_yield_data['Type (Peg)'].isin(selected_types)]
                else: st.warning("Pool Yields: Cannot filter by type: 'Type (Peg)' column missing.")
        except KeyError as e:
            st.error(f"Pool Yields: Error applying filters: Column '{e}' not found.")
            filtered_yield_data = pd.DataFrame()
        except Exception as e:
             st.error(f"Pool Yields: Unexpected error applying filters: {e}")
             filtered_yield_data = pd.DataFrame()

    st.divider()

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
        st.info(f"Displaying {len(filtered_yield_data)} pools from DefiLlama.")
        display_columns = ['Chain', 'Project', 'Asset Symbol', 'APY (%)', 'TVL (USD)', 'Issuer/Name', 'Type (Peg)']
        yield_data_display = filtered_yield_data[[col for col in display_columns if col in filtered_yield_data.columns]]
        column_config = {
            "TVL (USD)": st.column_config.TextColumn("TVL (USD)", help="Total Value Locked (Formatted)"),
            "APY (%)": st.column_config.TextColumn("APY (%)", help="Annual Percentage Yield (Formatted)"),
            "Issuer/Name": st.column_config.TextColumn("Issuer/Name", help="Issuing project or name (from metadata)"),
            "Type (Peg)": st.column_config.TextColumn("Type (Peg)", help="Peg type (from metadata)")
        }
        st.dataframe(yield_data_display, column_config=column_config, hide_index=True, use_container_width=True)


if choice == "Pool Yield Analytics":
    st.title("Pool Yield Analytics")
    st.write("Visualizations based on the broader stablecoin and yield-asset pool data from API (Default TVL > $10M).")

    stablecoin_metadata_api = get_stablecoin_metadata() 
    analytics_min_tvl_api = DEFAULT_MIN_TVL_USD
    st.info(f"Analytics based on API pools with TVL > {format_tvl(analytics_min_tvl_api)}")

    analytics_data_api = get_analytics_data(analytics_min_tvl_api, TARGET_YIELD_ASSET_SYMBOLS_LOWER, stablecoin_metadata_api)

    data_valid_analytics_api = not (isinstance(analytics_data_api, pd.DataFrame) and
                                  any(col in analytics_data_api.columns for col in ['error', 'warning', 'warning_tvl']))

    if data_valid_analytics_api and not analytics_data_api.empty:
        st.subheader("APY Distribution")
        try:
            if 'APY' in analytics_data_api.columns:
                apy_data_numeric = pd.to_numeric(analytics_data_api['APY'], errors='coerce').dropna()
                if len(apy_data_numeric) > 10:
                    q_low = apy_data_numeric.quantile(0.01); q_high = apy_data_numeric.quantile(0.99)
                    hist_data = analytics_data_api[(analytics_data_api['APY'] >= q_low) & (analytics_data_api['APY'] <= q_high)].copy()
                    hist_title = "Distribution of Pool APYs (1st-99th Percentile)"
                    if hist_data.empty: hist_data = analytics_data_api.copy(); hist_title = "Distribution of Pool APYs (API Data, All)"
                else: hist_data = analytics_data_api.copy(); hist_title = "Distribution of Pool APYs (API Data, All)"

                if not hist_data.empty:
                    fig_hist = px.histogram(hist_data, x="APY", nbins=50, title=hist_title, labels={'APY': 'Annual Percentage Yield (%)'}, marginal="box")
                    fig_hist.update_layout(bargap=0.1)
                    st.plotly_chart(fig_hist, use_container_width=True)
                else: st.warning("Pool Analytics: Not enough API data points for APY distribution.")
            else: st.warning("Pool Analytics: APY column not found in API data.")
        except Exception as e: st.warning(f"Pool Analytics: Could not generate APY Distribution plot: {e}")

        st.divider(); st.subheader("TVL vs. APY")
        try:
            if 'TVL_USD' in analytics_data_api.columns and 'APY' in analytics_data_api.columns and 'Project' in analytics_data_api.columns and 'Asset Symbol' in analytics_data_api.columns:
                if not analytics_data_api.empty:
                    hover_cols = ['Chain', 'Project', 'Issuer/Name', 'Type (Peg)', 'Type (Peg Mechanism)']
                    hover_cols_exist = [col for col in hover_cols if col in analytics_data_api.columns]
                    fig_scatter = px.scatter(
                        analytics_data_api, x="TVL_USD", y="APY", color="Project", size="TVL_USD",
                        hover_name="Asset Symbol", hover_data=hover_cols_exist, log_x=True,
                        title="Pool TVL vs. APY (Log Scale TVL)",
                        labels={'TVL_USD': 'Total Value Locked (USD - Log Scale)', 'APY': 'Annual Percentage Yield (%)'})
                    fig_scatter.update_layout(legend_title_text='Project')
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else: st.warning("Pool Analytics: Not enough API data points for TVL vs APY plot.")
            else: st.warning("Pool Analytics: Required columns missing for TVL vs APY plot.")
        except Exception as e: st.warning(f"Pool Analytics: Could not generate TVL vs APY plot: {e}")

        st.divider(); st.subheader("Top Pools by APY")
        try:
            if 'APY' in analytics_data_api.columns and 'Asset Symbol' in analytics_data_api.columns:
                top_n_apy = min(20, len(analytics_data_api))
                if top_n_apy >= 1:
                    top_apy_pools = analytics_data_api.nlargest(top_n_apy, 'APY')
                    hover_cols = ['Project', 'Chain', 'TVL_USD', 'Type (Peg)', 'Issuer/Name']
                    hover_cols_exist = [col for col in hover_cols if col in top_apy_pools.columns]
                    fig_bar_apy = px.bar(
                        top_apy_pools.sort_values('APY', ascending=True), x="APY", y="Asset Symbol", orientation='h',
                        title=f"Top {top_n_apy} Pools by APY",
                        labels={'APY': 'Annual Percentage Yield (%)', 'Asset Symbol': 'Asset Symbol'}, text='APY', hover_data=hover_cols_exist)
                    fig_bar_apy.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                    fig_bar_apy.update_layout(yaxis_title="Asset Symbol", xaxis_title="Annual Percentage Yield (%)", uniformtext_minsize=8, uniformtext_mode='hide')
                    st.plotly_chart(fig_bar_apy, use_container_width=True)
                else: st.warning("Pool Analytics: Not enough API data points for Top Pools by APY.")
            else: st.warning("Pool Analytics: Required columns missing for Top APY plot.")
        except Exception as e: st.warning(f"Pool Analytics: Could not generate Top Pools by APY plot: {e}")

        st.divider(); st.subheader("Top 10 Projects by TVL")
        try:
            if 'Project' in analytics_data_api.columns and 'TVL_USD' in analytics_data_api.columns:
                project_tvl = analytics_data_api.groupby('Project')['TVL_USD'].sum().reset_index()
                top_10_tvl_projects = project_tvl.nlargest(10, 'TVL_USD')
                if not top_10_tvl_projects.empty:
                    fig_top_tvl = px.bar(
                        top_10_tvl_projects.sort_values('TVL_USD', ascending=True), x='TVL_USD', y='Project', orientation='h',
                        title="Top 10 Projects by Summed TVL in Filtered Pools (API Data)",
                        labels={'TVL_USD': 'Total Value Locked (USD)', 'Project': 'Project'}, text='TVL_USD')
                    fig_top_tvl.update_traces(texttemplate='%{text:$,.2s}', textposition='outside')
                    fig_top_tvl.update_layout(yaxis_title="Project", xaxis_title="Total Value Locked (USD)", uniformtext_minsize=8, uniformtext_mode='hide')
                    st.plotly_chart(fig_top_tvl, use_container_width=True)
                else: st.warning("Pool Analytics: Could not determine Top 10 Projects by TVL (API Data).")
            else: st.warning("Pool Analytics: Cannot generate Top 10 Projects plot: Missing columns (API Data).")
        except Exception as e: st.warning(f"Pool Analytics: Could not generate Top Projects by TVL plot: {e}")

    elif isinstance(analytics_data_api, pd.DataFrame) and 'error' in analytics_data_api.columns:
        st.error(f"Pool Analytics: Failed to fetch or process API data - {analytics_data_api['error'].iloc[0]}")
    elif isinstance(analytics_data_api, pd.DataFrame) and ('warning' in analytics_data_api.columns or 'warning_tvl' in analytics_data_api.columns):
        if 'warning' in analytics_data_api.columns: st.warning(f"Pool Analytics: {analytics_data_api['warning'].iloc[0]}. No API pools matched base criteria.")
        elif 'warning_tvl' in analytics_data_api.columns: st.warning(f"Pool Analytics: {analytics_data_api['warning_tvl'].iloc[0]}. No API pools matched TVL criteria.")
        st.warning("Pool Analytics (API) may be incomplete due to data limitations.")
    else:
        st.warning("No API data available to generate pool yield analytics plots.")