
import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(layout="wide")


DEFILLAMA_YIELDS_API_URL = "https://yields.llama.fi/pools"
DEFILLAMA_STABLECOINS_API_URL = "https://stablecoins.llama.fi/stablecoins"
DEFAULT_MIN_TVL_USD = 10_000_000


TARGET_YIELD_ASSET_SYMBOLS = [
    'susdf', 'sgyd', 'arusd', 'yusd', 'ivlusd', 'sdola', 'wusdn', 'avusd',
    'syrupusdc', 'srusd', 'usds', 'stusr', 'crt', 'bold', 'stusd', 'susda',
    'cgusd', 'smoney', 'csusdl', 'susds', 'susn', 'usdy', 'usd3', 'usdo',
    'musdm', 'sdeusd', 'susde', 'usyc', 'crvusd', 'stkgho', 'scusd', 'susdx',
    'perenausd', 'usd0',
]
TARGET_YIELD_ASSETS_LOWER = list(set([a.lower() for a in TARGET_YIELD_ASSET_SYMBOLS]))



def format_tvl(tvl):
    if pd.isna(tvl) or not isinstance(tvl, (int, float)): return "N/A"
    if tvl >= 1_000_000_000: return f"${tvl / 1_000_000_000:.2f}B"
    if tvl >= 1_000_000: return f"${tvl / 1_000_000:.2f}M"
    if tvl >= 1_000: return f"${tvl / 1_000:.1f}K"
    return f"${tvl:.0f}"

def format_apy(apy):
    if pd.isna(apy) or not isinstance(apy, (int, float)): return "N/A"
    return f"{apy:.2f}%"

def format_metadata(value):
    return value if pd.notna(value) else "N/A"



@st.cache_data(ttl=1800)
def get_stablecoin_metadata(retries=3, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(DEFILLAMA_STABLECOINS_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'peggedAssets' not in data or not isinstance(data['peggedAssets'], list):
                st.error("Unexpected Stablecoin API response format.")
                return pd.DataFrame()
            meta_df = pd.DataFrame(data['peggedAssets'])
            meta_df = meta_df[['symbol', 'name', 'pegMechanism', 'pegType']].copy()
            meta_df['join_symbol'] = meta_df['symbol'].str.lower()
            return meta_df
        except requests.exceptions.RequestException as e:
            attempt += 1
            st.warning(f"Stablecoin Metadata API request failed (Attempt {attempt}/{retries}): {e}")
            if attempt < retries: time.sleep(delay)
            else: st.error(f"Failed to fetch Stablecoin Metadata after {retries} attempts.")
    return pd.DataFrame()


@st.cache_data(ttl=600)
def get_yield_data(min_tvl, target_yield_assets_lower, stablecoin_metadata_df_serialized, retries=3, delay=5):
    stablecoin_metadata_df = pd.read_json(stablecoin_metadata_df_serialized) if stablecoin_metadata_df_serialized else pd.DataFrame()
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(DEFILLAMA_YIELDS_API_URL, timeout=20)
            response.raise_for_status()
            data = response.json()
            if 'data' not in data or not isinstance(data['data'], list):
                 return pd.DataFrame(columns=['error']) # Indicate specific error type

            df = pd.DataFrame(data['data'])

            if 'stablecoin' not in df.columns: df['stablecoin'] = False
            else: df['stablecoin'] = pd.to_numeric(df['stablecoin'], errors='coerce').fillna(0).astype(bool)
            if 'symbol' not in df.columns: df['symbol'] = ''
            else: df['symbol'] = df['symbol'].astype(str)
            if 'tvlUsd' not in df.columns: df['tvlUsd'] = pd.NA
            df['tvlUsd'] = pd.to_numeric(df['tvlUsd'], errors='coerce')

            df['join_symbol'] = df['symbol'].str.lower()
            condition_is_stablecoin_flag = df['stablecoin'] == True
            condition_is_target_yield_asset = df['join_symbol'].isin(target_yield_assets_lower)
            relevant_pools_df = df[condition_is_stablecoin_flag | condition_is_target_yield_asset].copy()
            if relevant_pools_df.empty: return pd.DataFrame(columns=['warning'])

            tvl_condition = relevant_pools_df['tvlUsd'].fillna(0) > min_tvl
            filtered_tvl_df = relevant_pools_df[tvl_condition].copy()
            if filtered_tvl_df.empty: return pd.DataFrame(columns=['warning_tvl'])

            if not stablecoin_metadata_df.empty:
                merged_df = pd.merge(filtered_tvl_df, stablecoin_metadata_df, on='join_symbol', how='left', suffixes=('', '_meta'))
            else:
                merged_df = filtered_tvl_df
                if 'name' not in merged_df.columns: merged_df['name'] = None
                if 'pegMechanism' not in merged_df.columns: merged_df['pegMechanism'] = None

            cols_to_keep = ['chain', 'project', 'symbol', 'tvlUsd', 'apy'] # Basic required info
            meta_cols_to_add = ['name', 'pegMechanism'] # Info from metadata
            final_cols = [col for col in cols_to_keep if col in merged_df.columns] + \
                         [col for col in meta_cols_to_add if col in merged_df.columns]
            final_df = merged_df[final_cols].copy()

            final_df['apy'] = pd.to_numeric(final_df['apy'], errors='coerce')

            rename_mapping = {
                'chain': 'Chain', 'project': 'Project', 'symbol': 'Asset Symbol',
                'apy': 'APY (%)', 'tvlUsd': 'TVL (USD)',
                'name': 'Issuer/Name', 'pegMechanism': 'Type (Peg)'
            }
            final_df.rename(columns={k: v for k, v in rename_mapping.items() if k in final_df.columns}, inplace=True)

            final_df['TVL_Value'] = final_df['TVL (USD)'] # Keep numeric for potential use
            final_df['TVL (USD)'] = final_df['TVL (USD)'].apply(format_tvl)
            final_df['APY (%)'] = final_df['APY (%)'].apply(format_apy)
            if 'Issuer/Name' in final_df.columns: final_df['Issuer/Name'] = final_df['Issuer/Name'].apply(format_metadata)
            if 'Type (Peg)' in final_df.columns: final_df['Type (Peg)'] = final_df['Type (Peg)'].apply(format_metadata)

            final_df['apy_sort_col'] = pd.to_numeric(final_df['APY (%)'].astype(str).str.replace('%', '', regex=False), errors='coerce')
            final_df = final_df.sort_values(by='apy_sort_col', ascending=False, na_position='last').drop(columns=['apy_sort_col'])

            return final_df

        except requests.exceptions.RequestException as e:
            attempt += 1
            st.warning(f"Yield Pool API request failed (Attempt {attempt}/{retries}): {e}")
            if attempt < retries: time.sleep(delay)
            else: st.error(f"Failed to fetch Yield Pool data after {retries} attempts.")
    return pd.DataFrame(columns=['error'])

@st.cache_data(ttl=600)
def get_analytics_data(min_tvl, target_yield_assets_lower, stablecoin_metadata_df_serialized, retries=3, delay=5):
    stablecoin_metadata_df = pd.read_json(stablecoin_metadata_df_serialized) if stablecoin_metadata_df_serialized else pd.DataFrame()
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(DEFILLAMA_YIELDS_API_URL, timeout=20)
            response.raise_for_status()
            data = response.json()
            if 'data' not in data or not isinstance(data['data'], list): return pd.DataFrame(columns=['error'])
            df = pd.DataFrame(data['data'])

            if 'stablecoin' not in df.columns: df['stablecoin'] = False
            else: df['stablecoin'] = pd.to_numeric(df['stablecoin'], errors='coerce').fillna(0).astype(bool)
            if 'symbol' not in df.columns: df['symbol'] = ''
            else: df['symbol'] = df['symbol'].astype(str)
            if 'tvlUsd' not in df.columns: df['tvlUsd'] = pd.NA
            df['tvlUsd'] = pd.to_numeric(df['tvlUsd'], errors='coerce')
            if 'apy' not in df.columns: df['apy'] = pd.NA
            df['apy'] = pd.to_numeric(df['apy'], errors='coerce')

            df['join_symbol'] = df['symbol'].str.lower()
            condition_is_stablecoin_flag = df['stablecoin'] == True
            condition_is_target_yield_asset = df['join_symbol'].isin(target_yield_assets_lower)
            relevant_pools_df = df[condition_is_stablecoin_flag | condition_is_target_yield_asset].copy()
            if relevant_pools_df.empty: return pd.DataFrame(columns=['warning'])

            tvl_condition = relevant_pools_df['tvlUsd'].fillna(0) > min_tvl
            filtered_tvl_df = relevant_pools_df[tvl_condition].copy()
            if filtered_tvl_df.empty: return pd.DataFrame(columns=['warning_tvl'])

            if not stablecoin_metadata_df.empty:
                merged_df = pd.merge(filtered_tvl_df, stablecoin_metadata_df, on='join_symbol', how='left', suffixes=('', '_meta'))
            else:
                merged_df = filtered_tvl_df
                if 'name' not in merged_df.columns: merged_df['name'] = None
                if 'pegMechanism' not in merged_df.columns: merged_df['pegMechanism'] = None

            cols_to_keep = ['chain', 'project', 'symbol', 'tvlUsd', 'apy', 'name', 'pegMechanism']
            analytics_df = merged_df[[col for col in cols_to_keep if col in merged_df.columns]].copy()

            rename_mapping = {
                'chain': 'Chain', 'project': 'Project', 'symbol': 'Asset Symbol',
                'apy': 'APY', 'tvlUsd': 'TVL_USD',
                'name': 'Issuer/Name', 'pegMechanism': 'Type (Peg)'
            }
            analytics_df.rename(columns={k: v for k, v in rename_mapping.items() if k in analytics_df.columns}, inplace=True)

            analytics_df.dropna(subset=['APY', 'TVL_USD'], inplace=True)
            for col in ['Project', 'Chain', 'Type (Peg)', 'Issuer/Name', 'Asset Symbol']:
                 if col in analytics_df.columns:
                        analytics_df[col] = analytics_df[col].astype(str).fillna('N/A').replace('', 'N/A')

            return analytics_df
        except requests.exceptions.RequestException as e:
            attempt += 1; st.warning(f"Analytics: Yield Pool API request failed (Attempt {attempt}/{retries}): {e}")
            if attempt < retries: time.sleep(delay)
            else: st.error(f"Analytics: Failed to fetch Yield Pool data after {retries} attempts.")
    return pd.DataFrame(columns=['error'])



with st.sidebar:

    try:
        st.image("izun_partners_logo.jpeg")
    except FileNotFoundError:
        st.warning("Logo file not found.")
    st.title("Izun Dashboard")
    navigation_options = ["Overview", "Stablecoin Yields", "Stablecoin Yield Analytics"]
    choice = st.radio("Navigation", navigation_options)
    st.info("team@izun.io")


if choice == "Overview":
    st.title('Izun - Dashboard')
    st.markdown("""
        **Navigation Guide:**

        * **Stablecoin Yields** - Table showing the yields offered by different stablecoin projects.
        * **Stablecoin Yield Analytics** - Analytics dashboard on stablecoin market.

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
    st.title('Stablecoin Yields')
    st.caption(f"Data sourced from DeFiLlama | Last Refreshed: {pd.Timestamp.now(tz='Europe/London').strftime('%Y-%m-%d %H:%M:%S %Z')}")

    stablecoin_metadata = get_stablecoin_metadata()
    stablecoin_metadata_serialized = stablecoin_metadata.to_json() if not stablecoin_metadata.empty else None

    st.subheader("Filters")
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        min_tvl_input = st.number_input(
            label="Minimum TVL (USD)", min_value=0, max_value=10_000_000_000,
            value=DEFAULT_MIN_TVL_USD, step=1_000_000,
            help="Filter pools by minimum Total Value Locked in USD.", format="%d"
        )

    initial_yield_data = get_yield_data(min_tvl_input, TARGET_YIELD_ASSETS_LOWER, stablecoin_metadata_serialized)

    selected_symbols = []
    selected_types = []
    options_symbols = []
    options_types = []

    data_valid = (not initial_yield_data.empty and 'warning' not in initial_yield_data.columns and
                  'warning_tvl' not in initial_yield_data.columns and 'error' not in initial_yield_data.columns)

    if data_valid:
        if 'Asset Symbol' in initial_yield_data.columns: options_symbols = sorted(initial_yield_data['Asset Symbol'].unique())
        if 'Type (Peg)' in initial_yield_data.columns: options_types = sorted(initial_yield_data['Type (Peg)'].dropna().unique())
        with col2: selected_symbols = st.multiselect("Filter by Asset Symbol", options=options_symbols, default=[])
        with col3: selected_types = st.multiselect("Filter by Type (Peg)", options=options_types, default=[])
    else:
        with col2: st.multiselect("Filter by Asset Symbol", options=[], disabled=True)
        with col3: st.multiselect("Filter by Type (Peg)", options=[], disabled=True)

    filtered_yield_data = initial_yield_data.copy()
    if data_valid:
        if selected_symbols:
            if 'Asset Symbol' in filtered_yield_data.columns: filtered_yield_data = filtered_yield_data[filtered_yield_data['Asset Symbol'].isin(selected_symbols)]
        if selected_types:
            if 'Type (Peg)' in filtered_yield_data.columns: filtered_yield_data = filtered_yield_data[filtered_yield_data['Type (Peg)'].isin(selected_types)]

    st.divider()

    if not data_valid:
        if initial_yield_data.empty and not ('warning' in initial_yield_data.columns or 'warning_tvl' in initial_yield_data.columns or 'error' in initial_yield_data.columns): st.error("An unknown error occurred while fetching data.")
        elif 'error' in initial_yield_data.columns: pass # Error already shown
        elif 'warning' in initial_yield_data.columns: st.warning("No stablecoin pools or specified yield assets found in the initial API response.")
        elif 'warning_tvl' in initial_yield_data.columns: st.warning(f"No stablecoin/yield asset pools found with TVL > {format_tvl(min_tvl_input)}.")
    elif filtered_yield_data.empty:
         st.warning("No pools match the selected filter criteria (Asset Symbol / Type Peg).")
    else:
        st.info(f"Displaying {len(filtered_yield_data)} results from DeFiLlama.")
        display_columns = ['Chain', 'Project', 'Asset Symbol', 'APY (%)', 'TVL (USD)', 'Issuer/Name', 'Type (Peg)']
        yield_data_display = filtered_yield_data[[col for col in display_columns if col in filtered_yield_data.columns]]
        column_config = {
            "TVL (USD)": st.column_config.TextColumn("TVL (USD)", help="Total Value Locked"),
            "APY (%)": st.column_config.TextColumn("APY (%)", help="Annual Percentage Yield"),
            "Issuer/Name": st.column_config.TextColumn("Issuer/Name", help="Issuing project or name"),
            "Type (Peg)": st.column_config.TextColumn("Type (Peg)", help="Peg mechanism")
        }
        st.dataframe(yield_data_display, column_config=column_config, hide_index=True, use_container_width=True)


if choice == "Stablecoin Yield Analytics":
    st.title("Stablecoin Yield Analytics")
    st.write("Visualizations based on stablecoin and yield-asset pool data.")

    stablecoin_metadata = get_stablecoin_metadata()
    stablecoin_metadata_serialized = stablecoin_metadata.to_json() if not stablecoin_metadata.empty else None
    analytics_min_tvl = DEFAULT_MIN_TVL_USD
    st.info(f"Analytics based on pools with TVL > {format_tvl(analytics_min_tvl)}")

    analytics_data = get_analytics_data(analytics_min_tvl, TARGET_YIELD_ASSETS_LOWER, stablecoin_metadata_serialized)

    data_valid_analytics = (not analytics_data.empty and 'warning' not in analytics_data.columns and
                            'warning_tvl' not in analytics_data.columns and 'error' not in analytics_data.columns)

    if data_valid_analytics:
        st.subheader("APY Distribution")
        apy_limit = analytics_data['APY'].quantile(0.99)
        hist_data = analytics_data[analytics_data['APY'] <= apy_limit]
        if not hist_data.empty:
            fig_hist = px.histogram(hist_data, x="APY", nbins=50, title="Distribution of Pool APYs (Capped at 99th Percentile)", labels={'APY': 'Annual Percentage Yield (%)'}, marginal="box")
            fig_hist.update_layout(bargap=0.1); st.plotly_chart(fig_hist, use_container_width=True)
        else: st.warning("Not enough data points to display APY distribution after filtering outliers.")

        st.divider(); st.subheader("TVL vs. APY")
        if not analytics_data.empty:
            fig_scatter = px.scatter(analytics_data, x="TVL_USD", y="APY", color="Project", size="TVL_USD", hover_name="Asset Symbol", hover_data=['Chain', 'Project', 'Issuer/Name', 'Type (Peg)'], log_x=True, title="Pool TVL vs. APY (Log Scale for TVL)", labels={'TVL_USD': 'Total Value Locked (USD - Log Scale)', 'APY': 'Annual Percentage Yield (%)'})
            fig_scatter.update_layout(legend_title_text='Project'); st.plotly_chart(fig_scatter, use_container_width=True)
        else: st.warning("Not enough data points to display TVL vs APY scatter plot.")

        st.divider(); st.subheader("Top Pools by APY")
        top_n_apy = 20
        if len(analytics_data) >= 1:
            top_apy_pools = analytics_data.nlargest(min(top_n_apy, len(analytics_data)), 'APY')
            fig_bar_apy = px.bar(top_apy_pools.sort_values('APY', ascending=True), x="APY", y="Asset Symbol", orientation='h', title=f"Top {len(top_apy_pools)} Pools by APY", labels={'APY': 'Annual Percentage Yield (%)', 'Asset Symbol': 'Asset Symbol'}, text='APY', hover_data=['Project', 'Chain', 'TVL_USD', 'Type (Peg)'])
            fig_bar_apy.update_traces(texttemplate='%{text:.2f}%', textposition='outside'); fig_bar_apy.update_layout(yaxis_title="Asset Symbol", uniformtext_minsize=8, uniformtext_mode='hide'); st.plotly_chart(fig_bar_apy, use_container_width=True)
        else: st.warning("Not enough data points to display Top Pools by APY.")

        st.divider(); st.subheader("Top 10 Projects by Total Value Locked (TVL)")
        if 'Project' in analytics_data.columns and 'TVL_USD' in analytics_data.columns:
            project_tvl = analytics_data.groupby('Project')['TVL_USD'].sum().reset_index()
            top_10_tvl_projects = project_tvl.nlargest(10, 'TVL_USD')
            if not top_10_tvl_projects.empty:
                fig_top_tvl = px.bar(top_10_tvl_projects.sort_values('TVL_USD', ascending=True), x='TVL_USD', y='Project', orientation='h', title="Top 10 Projects by Summed TVL in Filtered Pools", labels={'TVL_USD': 'Total Value Locked (USD)', 'Project': 'Project'}, text='TVL_USD')
                fig_top_tvl.update_traces(texttemplate='$%{text:,.2s}', textposition='outside'); fig_top_tvl.update_layout(yaxis_title="Project", uniformtext_minsize=8, uniformtext_mode='hide'); st.plotly_chart(fig_top_tvl, use_container_width=True)
            else: st.warning("Could not determine Top 10 Projects by TVL.")
        else: st.warning("Cannot generate Top 10 Projects plot: Missing 'Project' or 'TVL_USD' column.")

    elif 'warning' in analytics_data.columns or 'warning_tvl' in analytics_data.columns:
        if 'warning' in analytics_data.columns: st.warning("Analytics: No stablecoin pools or specified yield assets found in the initial API response.")
        elif 'warning_tvl' in analytics_data.columns: st.warning(f"Analytics: No stablecoin/yield asset pools found with TVL > {format_tvl(analytics_min_tvl)}.")
    elif 'error' in analytics_data.columns: st.error("Analytics: Failed to fetch or process data for visualizations.")
    else: st.warning("No data available to generate analytics plots.")

