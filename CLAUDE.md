# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- Setup environment: `uv venv && source .venv/bin/activate`
- Install dependencies: `uv pip install -e ".[dev]"`
- Run application: `streamlit run main.py`
- Format code: `black . && isort .`
- Run type checking: `mypy .`

## Code Style Guidelines
- **Imports**: Group standard library imports first, third-party imports second, local imports last
- **Formatting**: Use consistent indentation (4 spaces)
- **Types**: Use explicit variable types where possible, especially in function signatures
- **Functions**: Use descriptive function names with `snake_case`
- **Error Handling**: Follow the pattern of using retries with exponential backoff for API calls
- **Caching**: Use `@st.cache_data` with appropriate TTL for API responses
- **Data Processing**: Follow pandas patterns for data manipulation and column selection
- **UI Components**: Group related UI elements in logical sections using `st.columns` and `with` blocks