'''
****
Create a virtual environment

Used to create env:
python3 -m venv DLpricer

Activate:
source DLpricer/bin/activate

Deactive:
deactivate


***

To run
streamlit run main.py

Types of learning models to try
Multi-layer perceptron (MLP)
Convolutional neural network (CNN) 
Recurrent neural network (RNN)
Long short-term memory (LSTM)
'''


#Import 
from operator import index
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os 
from scipy.stats import norm
from dune_client.client import DuneClient
from dune_client.query import QueryBase


with st.sidebar: 
    st.image("izun_partners_logo.jpeg")
    st.title("Stablecoin Dashboard")
    choice = st.radio("Navigation", ["Overview", "Yields","Liquidity","Analytics"])
    st.info("team@izun.io")


if choice == "Overview":
    st.title('Izun - Stablecoin Dashboard')
    '''

        Navigation Guide:
    
    Yields - Table showing the yields offered by different stablecoin projects
    
    Liquidity - Table showing the indicated liquidity in stablecoin markets
    
    Analytics - Full analytics dashboard on stablecoin market
    
    '''

    st.button('Update All Data')


if choice == "Yields":
    st.title('Stablecoin Yields')
    st.write('Table overview of stablecoin yields')
    
    # --- Configuration ---
    # !!! REPLACE THIS WITH THE QUERY ID OF THE QUERY YOU SAVED IN DUNE !!!
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
            return pd.DataFrame() # Return empty dataframe on error

    if DUNE_QUERY_ID == 0:
        st.warning("Please replace `DUNE_QUERY_ID = 0` in the script with the actual Query ID of your saved query in Dune.", icon="⚠️")
        st.stop()

    # Fetch and display the data
    data_df = fetch_dune_data(DUNE_QUERY_ID)

    if not data_df.empty:
        st.subheader("Query Results")

        # Display the DataFrame as a table in Streamlit
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


if choice == "Liquidity": 
    st.title('Stablecoin Liquidity')
    st.write('Table overview of stablecoin liquidity')

if choice == "Analytics": 
    def calculate_fixed_payments(current_payment, outstanding_amount):
    # Calculate the monthly fixed mortgage payment for the next year with a 10% fee
        fixed_payment = (current_payment * 1.15) * 12
        return fixed_payment

    def calculate_cash_flows(fixed_payment, outstanding_amount):
        # Calculate the monthly cash flows for the fixed payments
        cash_flows = []
        balance = outstanding_amount
        for i in range(12):
            interest = balance * 0.05 / 12
            principal = fixed_payment - interest
            balance -= principal
            cash_flows.append(fixed_payment)
        return cash_flows

    st.title("Stablecoin Analytics Dashboard")
    st.write('Graphs updated weekly - to refresh to live data go to Overview tab')

    current_payment = st.number_input("Enter your current monthly position:", min_value=0.01, step=0.01)
    outstanding_amount = st.number_input("Enter your funding rate in bps:", min_value=0.01, step=0.01)

    if st.button("Calculate"):
        fixed_payment = calculate_fixed_payments(current_payment, outstanding_amount)
        st.write("Your fixed mortgage payment per month for a year long contract would be:", int(fixed_payment/12))
        cash_flows = calculate_cash_flows(fixed_payment/12, outstanding_amount)
        cash_flows_df = pd.DataFrame({"Month": range(1, 13), "Payment": cash_flows})
        st.write("Monthly cash flows for the fixed payments:")
        st.dataframe(cash_flows_df)