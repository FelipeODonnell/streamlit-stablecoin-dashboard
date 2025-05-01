"""
Style guide and consistent formatting utilities for the dashboard.

This module defines standard formatting and style patterns to ensure
consistency across the application.
"""
import streamlit as st
from typing import Dict, Any, Optional, List, Tuple, Union

# Define color schemes for light and dark modes
LIGHT_COLOR_PALETTE = {
    "primary": "#4682B4",      # Steel Blue
    "secondary": "#1E88E5",    # Blue
    "accent": "#00ACC1",       # Cyan
    "success": "#4CAF50",      # Green
    "warning": "#FFC107",      # Amber
    "error": "#F44336",        # Red
    "neutral": "#9E9E9E",      # Grey
    "background": "#FFFFFF",   # White
    "text": "#333333",         # Dark grey
}

DARK_COLOR_PALETTE = {
    "primary": "#4682B4",      # Steel Blue
    "secondary": "#1E88E5",    # Blue
    "accent": "#00ACC1",       # Cyan
    "success": "#4CAF50",      # Green
    "warning": "#FFC107",      # Amber
    "error": "#F44336",        # Red
    "neutral": "#9E9E9E",      # Grey
    "background": "#111111",   # Dark background
    "text": "#F0F0F0",         # Light text
}

# Standard plot colors for consistent visualizations
PLOT_COLORS = [
    "#4682B4", "#1E88E5", "#00ACC1", "#4CAF50", 
    "#FFC107", "#F44336", "#9C27B0", "#FF9800",
    "#3F51B5", "#009688", "#795548", "#607D8B"
]

# Standard sizes for plots and UI elements
SIZING = {
    "plot_height_small": 400,
    "plot_height_medium": 600,
    "plot_height_large": 800,
    "plot_width": None,  # Uses container width
    "font_size_small": 12,
    "font_size_medium": 16,
    "font_size_large": 20,
    "sidebar_width": 300,
}

# Default column config for datatables
DEFAULT_COLUMN_CONFIGS = {
    "Chain": st.column_config.TextColumn("Chain", help="Blockchain where the pool is deployed"),
    "Project": st.column_config.TextColumn("Project", help="Project name or protocol"),
    "Asset Symbol": st.column_config.TextColumn("Asset Symbol", help="Token symbol"),
    "APY (%)": st.column_config.TextColumn("APY (%)", help="Annual Percentage Yield"),
    "TVL (USD)": st.column_config.TextColumn("TVL (USD)", help="Total Value Locked in USD"),
    "Issuer/Name": st.column_config.TextColumn("Issuer/Name", help="Token issuer or name"),
    "Type (Peg)": st.column_config.TextColumn("Type (Peg)", help="Peg type (e.g., USD, EUR)"),
    "Type (Peg Mechanism)": st.column_config.TextColumn("Type (Peg Mechanism)", help="Mechanism used for pegging"),
    "Description": st.column_config.TextColumn("Description", help="Details about the yield source"),
    "Ticker": st.column_config.TextColumn("Ticker", help="Token ticker symbol"),
    "Yield": st.column_config.TextColumn("Yield", help="Annual yield (%)"),
    "TVL": st.column_config.TextColumn("TVL", help="Total Value Locked"),
    "Staked Proportion": st.column_config.TextColumn("Staked %", help="Percentage of tokens staked"),
    "Strategy Type": st.column_config.TextColumn("Strategy Type", help="Yield generation strategy category"),
}

def get_color_palette():
    """
    Get the appropriate color palette based on the theme.
    
    Returns:
        Dictionary with color values
    """
    # Check if we can detect the theme
    try:
        is_dark_theme = st.get_option("theme.base") == "dark"
        return DARK_COLOR_PALETTE if is_dark_theme else LIGHT_COLOR_PALETTE
    except:
        # If we can't detect the theme, use dark theme by default
        return DARK_COLOR_PALETTE

# Standard plot templates
def get_default_plot_layout(
    title: str,
    x_axis_title: Optional[str] = None,
    y_axis_title: Optional[str] = None,
    show_legend: bool = True,
    height: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get default plot layout configuration for consistent styling.
    
    Args:
        title: Plot title
        x_axis_title: X-axis title
        y_axis_title: Y-axis title
        show_legend: Whether to show the legend
        height: Plot height in pixels
        
    Returns:
        Dictionary with layout configuration
    """
    colors = get_color_palette()
    
    return {
        "title": title,
        "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
        "height": height or SIZING["plot_height_medium"],
        "font": {"family": "Arial, sans-serif", "size": SIZING["font_size_medium"], "color": colors["text"]},
        "title_font": {"size": SIZING["font_size_large"], "color": colors["text"]},
        "xaxis": {
            "title": x_axis_title, 
            "showgrid": True, 
            "gridcolor": "#555555" if colors == DARK_COLOR_PALETTE else "#EEEEEE",
            "titlefont": {"color": colors["text"]},
            "tickfont": {"color": colors["text"]}
        },
        "yaxis": {
            "title": y_axis_title, 
            "showgrid": True, 
            "gridcolor": "#555555" if colors == DARK_COLOR_PALETTE else "#EEEEEE",
            "titlefont": {"color": colors["text"]},
            "tickfont": {"color": colors["text"]}
        },
        "showlegend": show_legend,
        "legend": {
            "orientation": "h", 
            "yanchor": "bottom", 
            "y": -0.2,
            "font": {"color": colors["text"]}
        },
        "paper_bgcolor": colors["background"],
        "plot_bgcolor": colors["background"],
        "hovermode": "closest",
    }


def get_dataframe_style_dict() -> Dict[str, Any]:
    """
    Get standardized Streamlit DataFrame display options.
    
    Returns:
        Dictionary with DataFrame display options
    """
    return {
        "use_container_width": True,
        "hide_index": True,
    }


def apply_ui_theme() -> None:
    """
    Apply consistent styling to the Streamlit UI elements.
    Should be called at the app startup.
    """
    colors = get_color_palette()
    
    # Apply CSS to respect dark mode
    st.markdown(f"""
    <style>
        /* Override background color but keep light/dark mode for most components */
        .stApp {{
            transition: background-color 0.5s;
        }}
        .stButton>button {{
            background-color: {colors["primary"]};
            color: white;
        }}
        .stTextInput>div>div>input {{
            border-color: {colors["primary"]};
        }}
        .stSelectbox>div>div>select {{
            border-color: {colors["primary"]};
        }}
        .stNumberInput>div>div>input {{
            border-color: {colors["primary"]};
        }}
        h1, h2, h3 {{
            color: {colors["primary"]};
        }}
    </style>
    """, unsafe_allow_html=True)


def format_section_header(title: str) -> None:
    """
    Display a consistently formatted section header.
    
    Args:
        title: Section title
    """
    colors = get_color_palette()
    
    st.markdown(f"""
    <h2 style='color: {colors["primary"]}; border-bottom: 2px solid {colors["primary"]}; 
    padding-bottom: 10px;'>{title}</h2>
    """, unsafe_allow_html=True)


def format_card(
    title: str,
    content: str,
    color: Optional[str] = None
) -> None:
    """
    Display information in a card-like container.
    
    Args:
        title: Card title
        content: Card content
        color: Card accent color
    """
    colors = get_color_palette()
    color = color or colors["primary"]
    card_bg = colors["background"]
    text_color = colors["text"]
    
    st.markdown(f"""
    <div style='background-color: {card_bg}; padding: 15px; border-radius: 5px; 
    border-top: 5px solid {color}; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>
        <h3 style='color: {color};'>{title}</h3>
        <p style='color: {text_color};'>{content}</p>
    </div>
    """, unsafe_allow_html=True)


def create_info_box(
    message: str,
    box_type: str = "info"
) -> None:
    """
    Create a consistent info/warning/error box.
    
    Args:
        message: Message to display
        box_type: Type of box ('info', 'warning', 'error', 'success')
    """
    if box_type == "info":
        st.info(message)
    elif box_type == "warning":
        st.warning(message)
    elif box_type == "error":
        st.error(message)
    elif box_type == "success":
        st.success(message)
    else:
        st.write(message)