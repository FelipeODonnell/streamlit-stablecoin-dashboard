# Izun Stablecoin Dashboard

A dashboard for tracking and analyzing stablecoin yields and performance metrics.

## Features

- **Stablecoin Yields**: Table of yield-bearing stablecoins with filtering capabilities
- **Stablecoin Analytics**: Visualizations and analysis of stablecoin yield data
- **Pool Yields**: Comprehensive table of DeFi pool yields from DefiLlama
- **Pool Yield Analytics**: Analysis and visualization of yield pool market data

## Installation

1. Clone the repository:
```bash
git clone https://github.com/izun/streamlit-stablecoin-dashboard.git
cd streamlit-stablecoin-dashboard
```

2. Install `uv` if you don't have it:
```bash
pip install uv
```

3. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

## Usage

1. Run the application:
```bash
streamlit run main.py
```

2. Navigate to the URL displayed in your terminal (typically http://localhost:8501)

## Project Structure

```
streamlit-stablecoin-dashboard/
├── main.py                # Main application entry point
├── pyproject.toml        # Project configuration and dependencies
├── .streamlit/           # Streamlit configuration
│   └── config.toml       # Streamlit theme configuration
├── utils/                # Utility functions
│   ├── __init__.py
│   ├── api.py            # API interaction functions
│   ├── caching.py        # Caching utilities
│   ├── config.py         # Configuration and constants
│   ├── data_processing.py # Data processing utilities
│   ├── error_handling.py # Error handling utilities
│   ├── formatting.py     # Value formatting functions
│   ├── security.py       # Security utilities
│   └── style_guide.py    # Styling guidelines
├── pages/                # Dashboard page modules
│   ├── __init__.py
│   ├── overview.py       # Overview page
│   ├── stablecoin_yields.py       # Stablecoin yields page
│   ├── stablecoin_analytics.py    # Stablecoin analytics page
│   ├── pool_yields.py             # Pool yields page
│   └── pool_yield_analytics.py    # Pool yield analytics page
├── components/           # Reusable UI components
│   ├── __init__.py
│   ├── data_display.py   # Data display components
│   ├── filters.py        # Filter components
│   └── sidebar.py        # Sidebar components
└── izun_partners_logo.jpeg # Logo file
```

## Development

- Update dependencies with uv:
```bash
uv pip install -e ".[dev]"
```

- Format code:
```bash
black .
isort .
```

- Run type checking:
```bash
mypy .
```

- For code changes, follow the established structure:
  - Add utility functions to the appropriate files in `utils/`
  - Add new pages in the `pages/` directory
  - Register new pages in `main.py`

## Contact

For questions or support, contact team@izun.io