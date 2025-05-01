"""
Visualization utilities for the stablecoin dashboard.
"""
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Optional, Tuple, Dict

def create_top_yield_plot(
    df: pd.DataFrame, 
    top_n: int = 20,
    color_column: Optional[str] = 'Strategy Type',
    hover_data_columns: Optional[List[str]] = None
) -> go.Figure:
    """
    Creates a horizontal bar chart showing top stablecoins by yield.
    
    Args:
        df: DataFrame containing the data
        top_n: Number of top assets to display
        color_column: Column to use for coloring the bars
        hover_data_columns: Columns to include in hover data
        
    Returns:
        Plotly figure object
    """
    if 'APY' not in df.columns or 'Asset Symbol' not in df.columns:
        logging.warning("Required columns (APY, Asset Symbol) not found for Top Yield plot.")
        fig = go.Figure()
        fig.update_layout(
            title="Cannot generate plot: Missing required data",
            annotations=[{
                'text': "Required columns not found in the dataset",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig
        
    try:
        # Select top n assets by APY
        top_n_yield = min(top_n, len(df))
        top_yield_df = df.nlargest(top_n_yield, 'APY')
        
        if top_yield_df.empty:
            logging.warning("Not enough data to display top stablecoins by yield.")
            return go.Figure()
            
        color_col = color_column if color_column in top_yield_df.columns else None
        hover_cols = [col for col in (hover_data_columns or []) if col in top_yield_df.columns]
        
        fig = px.bar(
            top_yield_df.sort_values('APY', ascending=True),
            x='APY', y='Asset Symbol', orientation='h',
            title=f"Top {top_n_yield} Stablecoins by Yield",
            labels={'APY': 'Annual Percentage Yield (%)', 'Asset Symbol': 'Asset Symbol'},
            text='APY', color=color_col, hover_data=hover_cols
        )
        
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(
            yaxis_title="Asset Symbol", 
            xaxis_title="Annual Percentage Yield (%)",
            uniformtext_minsize=8, 
            uniformtext_mode='hide',
            legend_title_text='Strategy Type' if color_col else None
        )
        
        return fig
        
    except Exception as e:
        logging.error(f"Error in Top Yield plot: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating plot",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig


def create_strategy_distribution_pie(df: pd.DataFrame) -> go.Figure:
    """
    Creates a pie chart showing distribution of stablecoins by strategy type.
    
    Args:
        df: DataFrame containing the data
        
    Returns:
        Plotly figure object
    """
    if 'Strategy Type' not in df.columns:
        logging.warning("Strategy Type information not available for distribution plot.")
        fig = go.Figure()
        fig.update_layout(
            title="Cannot generate plot: Missing Strategy Type data",
            annotations=[{
                'text': "Strategy Type column not found in the dataset",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig
        
    try:
        strategy_counts = df['Strategy Type'].value_counts().reset_index()
        strategy_counts.columns = ['Strategy Type', 'Count']
        
        if strategy_counts.empty:
            logging.warning("No strategy type data available.")
            return go.Figure()
            
        fig = px.pie(
            strategy_counts, values='Count', names='Strategy Type',
            title="Distribution by Strategy Type", hole=0.4
        )
        fig.update_traces(textinfo='percent+label')
        
        return fig
        
    except Exception as e:
        logging.error(f"Error in Strategy Distribution plot: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating plot",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig


def create_avg_yield_by_strategy_plot(df: pd.DataFrame) -> go.Figure:
    """
    Creates a bar chart showing average yield by strategy type.
    
    Args:
        df: DataFrame containing the data
        
    Returns:
        Plotly figure object
    """
    if 'Strategy Type' not in df.columns or 'APY' not in df.columns:
        logging.warning("Strategy Type or APY information not available for average yield plot.")
        fig = go.Figure()
        fig.update_layout(
            title="Cannot generate plot: Missing required data",
            annotations=[{
                'text': "Required columns not found in the dataset",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig
        
    try:
        strategy_avg_yield = df.groupby('Strategy Type')['APY'].mean().reset_index()
        strategy_avg_yield = strategy_avg_yield.sort_values('APY', ascending=False)
        
        if strategy_avg_yield.empty:
            logging.warning("Not enough data to display average yield by strategy type.")
            return go.Figure()
            
        fig = px.bar(
            strategy_avg_yield, x='Strategy Type', y='APY',
            title="Average Yield by Strategy Type",
            labels={'APY': 'Average Annual Percentage Yield (%)', 'Strategy Type': 'Strategy Type'},
            text='APY', color='Strategy Type'
        )
        
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(xaxis={'categoryorder': 'total descending'})
        
        return fig
        
    except Exception as e:
        logging.error(f"Error in Average Yield plot: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating plot",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig


def create_tvl_vs_apy_scatter(
    df: pd.DataFrame,
    color_column: Optional[str] = 'Strategy Type',
    hover_name: str = 'Asset Symbol',
    hover_data_columns: Optional[List[str]] = None
) -> go.Figure:
    """
    Creates a scatter plot showing TVL vs APY for stablecoins.
    
    Args:
        df: DataFrame containing the data
        color_column: Column to use for coloring the points
        hover_name: Column to use for hover labels
        hover_data_columns: Columns to include in hover data
        
    Returns:
        Plotly figure object
    """
    required_cols = ['TVL_USD', 'APY', hover_name]
    
    for col in required_cols:
        if col not in df.columns:
            logging.warning(f"Required column {col} not found for scatter plot.")
            fig = go.Figure()
            fig.update_layout(
                title="Cannot generate plot: Missing required data",
                annotations=[{
                    'text': f"Required column '{col}' not found in the dataset",
                    'showarrow': False,
                    'font': {'size': 14}
                }]
            )
            return fig
    
    try:
        if df.empty:
            logging.warning("Not enough data points to display TVL vs APY scatter plot.")
            return go.Figure()
            
        color_col = color_column if color_column in df.columns else None
        hover_cols = [col for col in (hover_data_columns or []) if col in df.columns]
        
        fig = px.scatter(
            df, x="TVL_USD", y="APY",
            color=color_col, size="TVL_USD",
            hover_name=hover_name, hover_data=hover_cols,
            log_x=True, title="TVL vs. APY (Log Scale TVL)",
            labels={
                'TVL_USD': 'Total Value Locked (USD - Log Scale)', 
                'APY': 'Annual Percentage Yield (%)'
            }
        )
        
        fig.update_layout(legend_title_text='Strategy Type' if color_col else "Project")
        
        return fig
        
    except Exception as e:
        logging.error(f"Error in TVL vs APY plot: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating plot",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig


def create_apy_distribution_histogram(df: pd.DataFrame) -> go.Figure:
    """
    Creates a histogram showing the distribution of APYs.
    
    Args:
        df: DataFrame containing the data
        
    Returns:
        Plotly figure object
    """
    if 'APY' not in df.columns:
        logging.warning("APY column not found in API data.")
        fig = go.Figure()
        fig.update_layout(
            title="Cannot generate plot: Missing APY data",
            annotations=[{
                'text': "APY column not found in the dataset",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig
        
    try:
        apy_data_numeric = pd.to_numeric(df['APY'], errors='coerce').dropna()
        
        if len(apy_data_numeric) > 10:
            # Filter out extreme values that may skew the visualization
            q_low = apy_data_numeric.quantile(0.01)
            q_high = apy_data_numeric.quantile(0.99)
            hist_data = df[(df['APY'] >= q_low) & (df['APY'] <= q_high)].copy()
            hist_title = "Distribution of Pool APYs (1st-99th Percentile)"
            
            if hist_data.empty:
                hist_data = df.copy()
                hist_title = "Distribution of Pool APYs (All)"
        else:
            hist_data = df.copy()
            hist_title = "Distribution of Pool APYs (All)"
            
        if hist_data.empty:
            logging.warning("Not enough data points for APY distribution.")
            return go.Figure()
            
        fig = px.histogram(
            hist_data, 
            x="APY", 
            nbins=50, 
            title=hist_title, 
            labels={'APY': 'Annual Percentage Yield (%)'},
            marginal="box"
        )
        
        fig.update_layout(bargap=0.1)
        
        return fig
        
    except Exception as e:
        logging.error(f"Could not generate APY Distribution plot: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating plot",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig


def create_top_projects_by_tvl(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Creates a horizontal bar chart showing top projects by TVL.
    
    Args:
        df: DataFrame containing the data
        top_n: Number of top projects to display
        
    Returns:
        Plotly figure object
    """
    if 'Project' not in df.columns or 'TVL_USD' not in df.columns:
        logging.warning("Cannot generate Top Projects plot: Missing columns.")
        fig = go.Figure()
        fig.update_layout(
            title="Cannot generate plot: Missing required data",
            annotations=[{
                'text': "Required columns not found in the dataset",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig
        
    try:
        project_tvl = df.groupby('Project')['TVL_USD'].sum().reset_index()
        top_n_tvl_projects = project_tvl.nlargest(top_n, 'TVL_USD')
        
        if top_n_tvl_projects.empty:
            logging.warning(f"Could not determine Top {top_n} Projects by TVL.")
            return go.Figure()
            
        fig = px.bar(
            top_n_tvl_projects.sort_values('TVL_USD', ascending=True),
            x='TVL_USD', y='Project', orientation='h',
            title=f"Top {top_n} Projects by Summed TVL",
            labels={'TVL_USD': 'Total Value Locked (USD)', 'Project': 'Project'},
            text='TVL_USD'
        )
        
        fig.update_traces(texttemplate='%{text:$,.2s}', textposition='outside')
        fig.update_layout(
            yaxis_title="Project", 
            xaxis_title="Total Value Locked (USD)",
            uniformtext_minsize=8, 
            uniformtext_mode='hide'
        )
        
        return fig
        
    except Exception as e:
        logging.error(f"Could not generate Top Projects by TVL plot: {e}")
        fig = go.Figure()
        fig.update_layout(
            title="Error creating plot",
            annotations=[{
                'text': f"Error: {str(e)}",
                'showarrow': False,
                'font': {'size': 14}
            }]
        )
        return fig