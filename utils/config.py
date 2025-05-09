"""
Configuration and constants for the dashboard.
"""

from typing import Any, Dict, List

# API endpoints
DEFILLAMA_YIELDS_API_URL = "https://yields.llama.fi/pools"
DEFILLAMA_STABLECOINS_API_URL = "https://stablecoins.llama.fi/stablecoins"
DEFILLAMA_PROTOCOL_API_URL = "https://api.llama.fi/protocols"

# API settings
DEFAULT_MIN_TVL_USD = 10_000_000
API_TIMEOUT = 20
API_RETRIES = 3
API_DELAY = 5

# Rate limiting settings
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_WINDOW_SECONDS = 60

# Caching settings
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 600  # 10 minutes
CACHE_TTL_LONG = 1800  # 30 minutes
CACHE_TTL_VERY_LONG = 3600  # 1 hour

# UI settings
LOGO_PATH = "izun_partners_logo.jpeg"
TITLE = "Izun Stablecoin Dashboard"
CONTACT_INFO = "team@izun.io"

# Navigation
DEFAULT_NAVIGATION_OPTIONS = [
    "Overview",
    "Stablecoin Yields",
    "Stablecoin Analytics",
    "Pool Yields",
    "Pool Yield Analytics",
]

# Target assets
TARGET_YIELD_ASSET_SYMBOLS_LOWER: List[str] = [
    "susdf",
    "sgyd",
    "arusd",
    "yusd",
    "ivlusd",
    "sdola",
    "wusdn",
    "avusd",
    "syrupusdc",
    "srusd",
    "usds",
    "stusr",
    "crt",
    "bold",
    "stusd",
    "susda",
    "cgusd",
    "smoney",
    "csusdl",
    "susds",
    "susn",
    "usdy",
    "usd3",
    "usdo",
    "musdm",
    "sdeusd",
    "susde",
    "usyc",
    "crvusd",
    "stkgho",
    "scusd",
    "susdx",
    "perenausd",
    "usd0",
]

# Manually entered stablecoin data
MANUAL_STABLECOIN_DATA: Dict[str, Dict[str, str]] = {
    "susdf": {
        "Project": "@FalconStables",
        "Ticker": "SUSDF",
        "Yield": "14.40%",
        "TVL": "$218M",
        "Description": "Diversified institutional trading strategies",
        "StakedProportion": "78.30%",
    },
    "sgyd": {
        "Project": "@GyroStable",
        "Ticker": "SGYD",
        "Yield": "10.20%",
        "TVL": "$60M",
        "Description": "native protocol yield",
        "StakedProportion": "1.42%",
    },
    "arusd": {
        "Project": "@protocol_fx",
        "Ticker": "ARUSD",
        "Yield": "8.27%",
        "TVL": "$23M",
        "Description": "restaking rewards, including points",
        "StakedProportion": "?",
    },
    "yusd": {
        "Project": "@GetYieldFi",
        "Ticker": "YUSD",
        "Yield": "10.24%",
        "TVL": "$12.9M",
        "Description": "allocates funds across defi bluechips",
        "StakedProportion": "N/A",
    },
    "ivlusd": {
        "Project": "@levelusds",
        "Ticker": "LVLUSD",
        "Yield": "9.28%",
        "TVL": "$167M",
        "Description": "lending/restaking",
        "StakedProportion": "34.62%",
    },
    "sdola": {
        "Project": "@InverseFinance",
        "Ticker": "SDOLA",
        "Yield": "6.91%",
        "TVL": "$25.5M",
        "Description": "native protocol yield",
        "StakedProportion": "35.85%",
    },
    "wusdn": {
        "Project": "@SmarDex",
        "Ticker": "WUSDN",
        "Yield": "17.8%",
        "TVL": "$2.2M",
        "Description": "delta neutral strategy",
        "StakedProportion": "?",
    },
    "avusd": {
        "Project": "@avantprotocol",
        "Ticker": "AVUSD",
        "Yield": "10.26%",
        "TVL": "$43.9M",
        "Description": "arb / cash & carry",
        "StakedProportion": "0.00%",
    },
    "syrupusdc": {
        "Project": "@syrupfi",
        "Ticker": "SYRUPUSDC",
        "Yield": "10.4%",
        "TVL": "$702.2M",
        "Description": "fixed-rate, overcollateralized loans",
        "StakedProportion": "N/A",
    },
    "srusd": {
        "Project": "@reya_xyz",
        "Ticker": "SRUSD",
        "Yield": "4.23%",
        "TVL": "$16M",
        "Description": "powers native DEX",
        "StakedProportion": "?",
    },
    "usds": {
        "Project": "@SperaxUSD",
        "Ticker": "USDS",
        "Yield": "3.01%",
        "TVL": "$895K",
        "Description": "collateral put to 3rd party DeFi protocols",
        "StakedProportion": "N/A",
    },
    "stusr": {
        "Project": "@ResolvLabs",
        "Ticker": "STUSR",
        "Yield": "1.9%",
        "TVL": "$344M",
        "Description": "delta neutral strategy",
        "StakedProportion": "18.25%",
    },
    "crt": {
        "Project": "@DeFiCarrot",
        "Ticker": "CRT",
        "Yield": "4.99%",
        "TVL": "$14M",
        "Description": "looks like a manual funds rebalances",
        "StakedProportion": "?",
    },
    "bold": {
        "Project": "@LiquityProtocol",
        "Ticker": "BOLD",
        "Yield": "5.91%",
        "TVL": "$24M",
        "Description": "native protocol revenues",
        "StakedProportion": "N/A",
    },
    "stusd": {
        "Project": "@AngleProtocol",
        "Ticker": "STUSD",
        "Yield": "8.1%",
        "TVL": "$28.1M",
        "Description": "RWAs & borrower interest yield",
        "StakedProportion": "N/A",
    },
    "susda": {
        "Project": "@avalonfinance_",
        "Ticker": "SUSDA",
        "Yield": "5%",
        "TVL": "$185.8M",
        "Description": "revenue generated through USDaLend",
        "StakedProportion": "N/A",
    },
    "cgusd": {
        "Project": "@CygnusFi",
        "Ticker": "CGUSD",
        "Yield": "4.84%",
        "TVL": "$37.6M",
        "Description": "T-bills",
        "StakedProportion": "N/A",
    },
    "smoney": {
        "Project": "@defidotmoney",
        "Ticker": "SMONEY",
        "Yield": "9.84%",
        "TVL": "$172K",
        "Description": "native protocol revenues",
        "StakedProportion": "41.22%",
    },
    "csusdl": {
        "Project": "@OxCoinshift",
        "Ticker": "CSUSDL",
        "Yield": "3.69%",
        "TVL": "$70.9M",
        "Description": "USDL (by paxos) Morpho Vault + rewards",
        "StakedProportion": "88.04%",
    },
    "susds": {
        "Project": "@SkyEcosystem",
        "Ticker": "SUSDS",
        "Yield": "4.50%",
        "TVL": "$2.48M",
        "Description": "Sky Savings Rate",
        "StakedProportion": "?",
    },
    "susn": {
        "Project": "@noon_capital",
        "Ticker": "SUSN",
        "Yield": "4.53%",
        "TVL": "$27.6M",
        "Description": "t-bills & delta neutral strats",
        "StakedProportion": "45.97%",
    },
    "usdy": {
        "Project": "@OndoFinance",
        "Ticker": "USDY",
        "Yield": "4.25%",
        "TVL": "$585.34M",
        "Description": "T-bills",
        "StakedProportion": "N/A",
    },
        "ousg": {
        "Project": "@OndoFinance",
        "Ticker": "OUSG",
        "Yield": "4.07%",
        "TVL": "$497.85M",
        "Description": "T-bills",
        "StakedProportion": "N/A",
    },
    "usd3": {
        "Project": "@reserveprotocol",
        "Ticker": "USD3",
        "Yield": "3.1%",
        "TVL": "$5.78M",
        "Description": "Index of different holdings, lateral exposure to aave, comp, morpho",
        "StakedProportion": "N/A",
    },
    "usdo": {
        "Project": "@OpenEden_X",
        "Ticker": "USDO",
        "Yield": "4.03%",
        "TVL": "$149.1M",
        "Description": "T-bills",
        "StakedProportion": "43.94%",
    },
    "musdm": {
        "Project": "@MountainUSD",
        "Ticker": "MUSDM",
        "Yield": "3.80%",
        "TVL": "$35M",
        "Description": "T-bills",
        "StakedProportion": "N/A",
    },
    "sdeusd": {
        "Project": "@elixir",
        "Ticker": "SDEUSD",
        "Yield": "3.79%",
        "TVL": "$177.5M",
        "Description": "mixture of treasuries and funding yield",
        "StakedProportion": "72.41%",
    },
    "susde": {
        "Project": "@ethena_labs",
        "Ticker": "SUSDE",
        "Yield": "4.4%",
        "TVL": "$4.4B",
        "Description": "perps funding & staked eth",
        "StakedProportion": "43.20%",
    },
    "usyc": {
        "Project": "@Hashnote_Labs",
        "Ticker": "USYC",
        "Yield": "3.86%",
        "TVL": "$664.5M",
        "Description": "T-bills",
        "StakedProportion": "N/A",
    },
    "crvusd": {
        "Project": "@curvefinance",
        "Ticker": "CRVUSD",
        "Yield": "1.1%",
        "TVL": "$208.8M",
        "Description": "interest paid by crUSD minters",
        "StakedProportion": "N/A",
    },
    "stkgho": {
        "Project": "@aave",
        "Ticker": "STKGHO",
        "Yield": "3.65%",
        "TVL": "$159M",
        "Description": "Aave Safety Module",
        "StakedProportion": "N/A",
    },
    "scusd": {
        "Project": "@Rings_Protocol",
        "Ticker": "SCUSD",
        "Yield": "5.13%",
        "TVL": "$110.8M",
        "Description": "farming strategies via Veda vaults",
        "StakedProportion": "63.56%",
    },
    "susdx": {
        "Project": "@StablesLabs",
        "Ticker": "SUSDX",
        "Yield": "4.27%",
        "TVL": "$627M",
        "Description": "Delta Neutral",
        "StakedProportion": "N/A",
    },
    "perenausd": {
        "Project": "@PerenaUSD",
        "Ticker": "PERENAUSD",
        "Yield": "1.25%",
        "TVL": "$26.5M",
        "Description": "swap fees of native Growth Pools",
        "StakedProportion": "N/A",
    },
    "usd0": {
        "Project": "@Usualmoney",
        "Ticker": "USD0",
        "Yield": "11%",
        "TVL": "$651.7M",
        "Description": "max{Treasury, Option}",
        "StakedProportion": "N/A",
    },
}
