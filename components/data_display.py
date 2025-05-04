"""
Reusable data display components for the Stablecoin Dashboard.
"""

# Standard library imports
from typing import Any, Callable, Dict, List, Optional, Union

# Third-party imports
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Local imports
from utils.style_guide import (
    DEFAULT_COLUMN_CONFIGS,
    get_dataframe_style_dict,
    get_default_plot_layout,
)


def display_dataframe(
    df: pd.DataFrame,
    column_config: Optional[Dict[str, Any]] = None,
    use_container_width: bool = True,
    hide_index: bool = True,
    height: Optional[int] = None,
    width: Optional[int] = None,
) -> None:
    """
    Display a DataFrame with consistent styling.

    Args:
        df: DataFrame to display
        column_config: Column configuration for the DataFrame
        use_container_width: Whether to use the full container width
        hide_index: Whether to hide the index
        height: Height of the DataFrame
        width: Width of the DataFrame
    """
    # Get default styling
    style_dict = get_dataframe_style_dict()

    # Override with provided parameters
    if not use_container_width:
        style_dict["use_container_width"] = False
    if not hide_index:
        style_dict["hide_index"] = False
    if height:
        style_dict["height"] = height
    if width:
        style_dict["width"] = width

    # Get column configuration
    if column_config is None:
        # Use default column configs for columns that exist in the DataFrame
        column_config = {
            col: DEFAULT_COLUMN_CONFIGS.get(col, st.column_config.TextColumn(col))
            for col in df.columns
            if col in DEFAULT_COLUMN_CONFIGS
        }

    # Display the DataFrame
    if df.empty:
        st.warning("No data available to display.")
    else:
        st.dataframe(df, column_config=column_config, **style_dict)


def display_metric_cards(
    metrics: Dict[str, Union[float, int, str]],
    columns: int = 3,
    format_func: Optional[Dict[str, Callable]] = None,
) -> None:
    """
    Display multiple metrics in card format.

    Args:
        metrics: Dictionary of metric names and values
        columns: Number of columns to display
        format_func: Dictionary of formatting functions for each metric
    """
    if not metrics:
        return

    cols = st.columns(columns)

    for i, (label, value) in enumerate(metrics.items()):
        col_idx = i % columns

        # Apply formatting function if provided
        if format_func and label in format_func:
            formatted_value = format_func[label](value)
        else:
            formatted_value = value

        cols[col_idx].metric(label=label, value=formatted_value)


def display_plotly_chart(
    fig: go.Figure,
    use_container_width: bool = True,
    title: Optional[str] = None,
    x_axis_title: Optional[str] = None,
    y_axis_title: Optional[str] = None,
    height: Optional[int] = None,
    show_legend: bool = True,
) -> None:
    """
    Display a Plotly chart with consistent styling.

    Args:
        fig: Plotly figure to display
        use_container_width: Whether to use the full container width
        title: Chart title (overrides existing title)
        x_axis_title: X-axis title (overrides existing title)
        y_axis_title: Y-axis title (overrides existing title)
        height: Chart height
        show_legend: Whether to show the legend
    """
    # Apply default layout for consistency
    layout = get_default_plot_layout(
        title=title or fig.layout.title.text or "",
        x_axis_title=x_axis_title,
        y_axis_title=y_axis_title,
        show_legend=show_legend,
        height=height,
    )

    # Update the figure layout
    fig.update_layout(**layout)

    # Display the chart
    st.plotly_chart(fig, use_container_width=use_container_width)


def display_data_summary(
    df: pd.DataFrame, title: str = "Data Summary", include_stats: bool = True
) -> None:
    """
    Display a summary of the DataFrame.

    Args:
        df: DataFrame to summarize
        title: Title for the summary
        include_stats: Whether to include descriptive statistics
    """
    if df.empty:
        st.warning("No data available for summary.")
        return

    st.subheader(title)

    # Create summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rows", len(df))
    col2.metric("Total Columns", len(df.columns))

    # If specific columns exist, show their stats
    numeric_cols = df.select_dtypes(include=["int", "float"]).columns

    if "TVL_USD" in numeric_cols:
        col3.metric("Total TVL", f"${df['TVL_USD'].sum():,.2f}")
    elif "TVL_Value" in numeric_cols:
        col3.metric("Total TVL", f"${df['TVL_Value'].sum():,.2f}")

    # Include descriptive statistics if requested
    if include_stats and len(numeric_cols) > 0:
        st.subheader("Descriptive Statistics")
        stats_df = df[numeric_cols].describe().T
        display_dataframe(stats_df, hide_index=False)


def display_info_alert(message: str, alert_type: str = "info") -> None:
    """
    Display an alert message with consistent styling.

    Args:
        message: Message to display
        alert_type: Type of alert ('info', 'warning', 'error', 'success')
    """
    if alert_type == "info":
        st.info(message)
    elif alert_type == "warning":
        st.warning(message)
    elif alert_type == "error":
        st.error(message)
    elif alert_type == "success":
        st.success(message)
    else:
        st.write(message)


def display_data_download(
    df: pd.DataFrame,
    filename: str = "data.csv",
    label: str = "Download Data",
    help_text: str = "Download the data as a CSV file",
    mime: str = "text/csv",
) -> None:
    """
    Create a download button for DataFrame.

    Args:
        df: DataFrame to download
        filename: Name of the file to download
        label: Label for the download button
        help_text: Help text for the download button
        mime: MIME type of the file
    """
    if df.empty:
        st.warning("No data available to download.")
        return

    # Convert DataFrame to CSV
    csv = df.to_csv(index=False)

    # Create download button
    st.download_button(label=label, data=csv, file_name=filename, mime=mime, help=help_text)


def create_tabs(tab_names: List[str]) -> List[st.tab]:
    """
    Create a set of tabs.

    Args:
        tab_names: List of tab names

    Returns:
        List of tab objects
    """
    return st.tabs(tab_names)
