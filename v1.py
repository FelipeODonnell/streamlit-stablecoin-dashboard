import streamlit as st
import os
import pandas as pd
from dune_client.client import DuneClient
from dune_client.query import QueryBase
# No QueryParameter needed as the SQL has no {{parameters}}

# --- Configuration ---
# !!! REPLACE THIS WITH THE QUERY ID OF THE QUERY YOU SAVED IN DUNE !!!
# Find this in the URL after saving your SQL in the Dune interface
# e.g., https://dune.com/queries/1234567 -> QUERY_ID = 1234567
DUNE_QUERY_ID = 4989107 # Replace with your actual Query ID from Dune

# --- Load API Key (Securely) ---
try:
    # Try Streamlit secrets first (recommended)
    dune_api_key = st.secrets["DUNE_API_KEY"]
except (KeyError, FileNotFoundError):
    # Fallback to environment variable if secrets file not found/key missing
    st.info("Dune API Key not found in st.secrets, checking environment variables...")
    dune_api_key = os.environ.get("DUNE_API_KEY")

if not dune_api_key:
    st.error("Dune API Key not found. Please set it in Streamlit secrets (`.streamlit/secrets.toml`) or as an environment variable `DUNE_API_KEY`.")
    st.stop() # Stop execution if key is missing
else:
    # Initialize Dune Client only if key is found
    try:
        dune = DuneClient(dune_api_key)
    except Exception as e:
        st.error(f"Failed to initialize Dune Client: {e}")
        st.stop()

# --- Function to Fetch Data (with Caching) ---
@st.cache_data(ttl=3600) # Cache results for 1 hour (3600 seconds)
def fetch_dune_data(query_id):
    """Fetches data from Dune API for a given query ID."""
    st.info(f"Fetching data from Dune for Query ID: {query_id}...")
    try:
        # Create a Query object using the saved Query ID
        query = QueryBase(query_id=query_id)
        # Execute the query and get results as a Pandas DataFrame
        results_df = dune.run_query_dataframe(query=query)
        st.success("Data fetched successfully!")
        return results_df
    except Exception as e:
        st.error(f"Error fetching data from Dune API: {e}")
        # You might want more specific error handling here
        # Check dune_client documentation or error message for details
        # e.g., check for authentication errors, query not found, execution errors
        return pd.DataFrame() # Return empty dataframe on error

# --- Streamlit App Layout ---
st.set_page_config(layout="wide") # Use wider layout for tables
st.title("Stablecoin Dashboard")
st.markdown(f"""
Stablecoin Dashboard - Graphs to be added & data updated periodically.
Data is cached for 1 hour.
""")

if DUNE_QUERY_ID == 0:
     st.warning("Please replace `DUNE_QUERY_ID = 0` in the script with the actual Query ID of your saved query in Dune.", icon="⚠️")
     st.stop()


# Fetch and display the data
data_df = fetch_dune_data(DUNE_QUERY_ID)

if not data_df.empty:
    st.subheader("Query Results")

    # Display the DataFrame as a table in Streamlit
    # Streamlit's dataframe renderer might automatically handle the HTML link in the 'CA' column.
    # If links don't work, you might need to use st.markdown with unsafe_allow_html=True
    # and build the table HTML manually, but try st.dataframe first.
    st.dataframe(data_df, use_container_width=True) # use_container_width helps fit the table

    st.caption(f"Displaying {len(data_df)} rows.")

    # Provide download button
    @st.cache_data # Cache the conversion
    def convert_df_to_csv(df):
       return df.to_csv(index=False).encode('utf-8')

    csv = convert_df_to_csv(data_df)
    st.download_button(
       label="Download data as CSV",
       data=csv,
       file_name=f'dune_query_{DUNE_QUERY_ID}_results.csv',
       mime='text/csv',
    )

else:
    st.warning("No data retrieved. This could be due to an API error, the query returning no results, or the query failing execution on Dune's side. Check the error message above if available.")

# --- To Run the App ---
# 1. Save this code as a Python file (e.g., `dune_app.py`).
# 2. Make sure you have your DUNE_API_KEY in `.streamlit/secrets.toml` or as an environment variable.
# 3. Replace `DUNE_QUERY_ID = 0` with the correct ID.
# 4. Open your terminal in the project directory.
# 5. Run: streamlit run dune_app.py