"""
Reusable filter components for the Stablecoin Dashboard.
"""

# Standard library imports
from typing import Any, Callable, Dict, List, Optional, Tuple

# Third-party imports
import pandas as pd
import streamlit as st

# Local imports
from utils.security import sanitize_filter_value


def create_text_filter(
    label: str, key: str, placeholder: str = "", help_text: str = "", disabled: bool = False
) -> str:
    """
    Create a text input filter component.

    Args:
        label: Label for the filter
        key: Unique key for the component
        placeholder: Placeholder text
        help_text: Help text for the filter
        disabled: Whether the filter is disabled

    Returns:
        Filter value entered by user
    """
    filter_value = st.text_input(
        label=label, placeholder=placeholder, key=key, help=help_text, disabled=disabled
    )
    # Sanitize the input value for security
    return sanitize_filter_value(filter_value)


def create_numeric_filter(
    label: str,
    key: str,
    min_value: float = 0.0,
    max_value: float = 1000000000.0,
    value: float = 0.0,
    step: float = 1.0,
    format: str = "%f",
    help_text: str = "",
    disabled: bool = False,
) -> float:
    """
    Create a numeric input filter component.

    Args:
        label: Label for the filter
        key: Unique key for the component
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        value: Default value
        step: Step size for the input
        format: Format string for displaying the value
        help_text: Help text for the filter
        disabled: Whether the filter is disabled

    Returns:
        Numeric filter value
    """
    return st.number_input(
        label=label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        step=step,
        format=format,
        key=key,
        help=help_text,
        disabled=disabled,
    )


def create_select_filter(
    label: str,
    options: List[Any],
    key: str,
    index: int = 0,
    help_text: str = "",
    disabled: bool = False,
) -> Any:
    """
    Create a select box filter component.

    Args:
        label: Label for the filter
        options: List of options to select from
        key: Unique key for the component
        index: Index of the default selected option
        help_text: Help text for the filter
        disabled: Whether the filter is disabled

    Returns:
        Selected filter value
    """
    return st.selectbox(
        label=label, options=options, index=index, key=key, help=help_text, disabled=disabled
    )


def create_multi_select_filter(
    label: str,
    options: List[Any],
    key: str,
    default: Optional[List[Any]] = None,
    help_text: str = "",
    disabled: bool = False,
) -> List[Any]:
    """
    Create a multi-select filter component.

    Args:
        label: Label for the filter
        options: List of options to select from
        key: Unique key for the component
        default: Default selected options
        help_text: Help text for the filter
        disabled: Whether the filter is disabled

    Returns:
        List of selected filter values
    """
    return st.multiselect(
        label=label,
        options=options,
        default=default or [],
        key=key,
        help=help_text,
        disabled=disabled,
    )


def filter_dataframe(df: pd.DataFrame, filters: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Apply multiple filters to a DataFrame.

    Args:
        df: DataFrame to filter
        filters: Dictionary of filter configurations
            {
                'column_name': {
                    'type': 'text'|'numeric'|'select',
                    'value': filter_value,
                    'condition': filter_condition_func (optional),
                    'case_sensitive': bool (optional, for text filters)
                },
                ...
            }

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    filtered_df = df.copy()

    for column, filter_config in filters.items():
        if column not in filtered_df.columns:
            st.warning(f"Column '{column}' not found in DataFrame, skipping filter")
            continue

        filter_type = filter_config.get("type", "text")
        filter_value = filter_config.get("value")

        # Skip if no filter value is provided
        if filter_value is None or (isinstance(filter_value, str) and filter_value == ""):
            continue

        if filter_type == "text":
            case_sensitive = filter_config.get("case_sensitive", False)

            if case_sensitive:
                condition = filtered_df[column].astype(str).str.contains(filter_value)
            else:
                condition = (
                    filtered_df[column]
                    .astype(str)
                    .str.lower()
                    .str.contains(str(filter_value).lower())
                )

            filtered_df = filtered_df[condition]

        elif filter_type == "numeric":
            condition_func = filter_config.get("condition", lambda col, val: col >= val)
            condition = condition_func(filtered_df[column], filter_value)
            filtered_df = filtered_df[condition]

        elif filter_type == "select":
            if isinstance(filter_value, list):
                if len(filter_value) > 0 and filter_value[0] != "All":
                    filtered_df = filtered_df[filtered_df[column].isin(filter_value)]
            elif filter_value != "All":
                filtered_df = filtered_df[filtered_df[column] == filter_value]

    return filtered_df


def create_filter_section(
    title: str = "Filters", columns: Optional[int] = None
) -> List[st.columns]:
    """
    Create a filter section with an optional title and columns.

    Args:
        title: Title for the filter section
        columns: Number of columns for the filter layout (None for no columns)

    Returns:
        List of column objects if columns is specified, otherwise empty list
    """
    st.subheader(title)

    if columns is not None and columns > 0:
        return st.columns(columns)
    return []
