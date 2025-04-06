import streamlit as st

st.set_page_config(page_title="Market Pulse", layout="wide")
st.title("📊 Welcome to MarketPulse Dashboard")

st.write("""
Real-Time Market Intelligence, Simplified.
""")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/Correlation-Heatmap.py", label="Correlation Heatmap", icon="📊")
    # Placeholder links – create pages like `Top_Setup.py` for these
    st.page_link("pages/Top_Setup.py", label="Top Setup", icon="📍")
    st.page_link("pages/Data_Scanner.py", label="Data Scanner", icon="🔍")
    

with col2:
    st.page_link("pages/NSE_Financial_Dashboard.py", label="NSE Financial Dashboard", icon="📉")
    st.page_link("pages/Market_Pulse_Score.py", label="Market Pulse Score", icon="📈")
    st.page_link("pages/COT_Asset_Data.py", label="COT Data", icon="📂")
    st.page_link("pages/COT_Data_History.py", label="Smart Money Indicator", icon="🕰️")


