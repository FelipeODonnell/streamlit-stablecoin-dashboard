"""
Overview page of the dashboard.
"""
import streamlit as st


def show_overview():
    """Display the overview page with information about different sections."""
    st.title('Izun - Dashboard')
    st.markdown("""
        * **Stablecoin Yields**: Table of yield-bearing stablecoins.
        * **Stablecoin Analytics**: Analytics from the data in the 'Stablecoin Yields' section.
        * **Pool Yields**: Table showing yields for all asset pools on DefiLlama.
        * **Pool Yield Analytics**: Analytics dashboard on the asset pool market.

        **Link to external stablecoin dashboards:**

        * Artemis: [https://app.artemisanalytics.com/stablecoins](https://app.artemisanalytics.com/stablecoins)
        * Stablecoin.wtf: [https://stablecoins.wtf/](https://stablecoins.wtf/)
        * Footprint: [https://www.footprint.network/@DamonSalvatore/Stablecoin-Dashboard?channel=ENG-260](https://www.footprint.network/@DamonSalvatore/Stablecoin-Dashboard?channel=ENG-260)
        * Orbital: [https://www.getorbital.com/stablecoin-dashboard](https://www.getorbital.com/stablecoin-dashboard)
        * Defi Llama: [https://defillama.com/stablecoins](https://defillama.com/stablecoins)
        * RWA.xyz: [https://app.rwa.xyz/stablecoins](https://app.rwa.xyz/stablecoins)
        * IntoTheBlock: [https://app.intotheblock.com/perspectives/stablecoins](https://app.intotheblock.com/perspectives/stablecoins)
    """)