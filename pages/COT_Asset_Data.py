import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from cot_reports import cot_year

# Streamlit settings
st.set_page_config(page_title="COT Report (2025)", layout="wide")
st.title("📊 COT Report - Asset Tracker")

# Asset mappings
assets = {
    "ZAR": "So African Rand", "GBP": "EURO FX/BRITISH POUND XRATE", "COPPER": "Copper",
    "JPY": "Japanese Yen", "US10T": "ULTRA UST 10Y", "USOil": "Crude Oil",
    "EUR": "Euro", "USD": "USD INDEX", "CAD": "Canadian Dollar", "SILVER": "Silver",
    "CHF": "Swiss Franc", "BTC": "Bitcoin", "Gold": "GOLD", "AUD": "Australian Dollar",
    "RUSSELL": "RUSSELL 2000 ANNUAL DIVIDEND", "NZD": "NZ DOLLAR", "NIKKEI": "NIKKEI STOCK AVERAGE YEN DENOM",
    "PLATINUM": "Platinum", "NASDAQ": "NASDAQ-100 Consolidated", "SPX": "S&P 500 ANNUAL DIVIDEND INDEX",
    "DOW": "DOW JONES U.S. REAL ESTATE IDX"
}

display_names = {
    "ZAR": "South African Rand", "GBP": "British Pound Sterling", "COPPER": "Copper Metal",
    "JPY": "Japanese Yen", "US10T": "US 10-Year Treasury", "USOil": "Crude Oil (WTI)",
    "EUR": "Euro Currency", "USD": "US Dollar Index", "CAD": "Canadian Dollar (CAD)", 
    "SILVER": "Silver Commodity", "CHF": "Swiss Franc (CHF)", "BTC": "Bitcoin (BTC)",
    "Gold": "GOLD", "AUD": "Australian Dollar (AUD)", "RUSSELL": "Russell 2000 Index",
    "NZD": "New Zealand Dollar", "NIKKEI": "Nikkei 225 Stock Index", 
    "PLATINUM": "Platinum Metal", "NASDAQ": "NASDAQ-100 Index", "SPX": "S&P 500 ANNUAL DIVIDEND INDEX",
    "DOW": "Dow Jones Industrial Average"
}

# Load 2025 COT data
@st.cache_data
def get_cot_data():
    df = cot_year(2025, cot_report_type="legacy_fut", store_txt=False, verbose=True)
    df["As of Date in Form YYYY-MM-DD"] = pd.to_datetime(df["As of Date in Form YYYY-MM-DD"])

    df = df[["As of Date in Form YYYY-MM-DD", "Market and Exchange Names", 
             "Noncommercial Positions-Long (All)", "Noncommercial Positions-Short (All)"]]
    
    df = df.rename(columns={
        "Market and Exchange Names": "Asset",
        "Noncommercial Positions-Long (All)": "Long",
        "Noncommercial Positions-Short (All)": "Short"
    })

    df["Asset"] = df["Asset"].apply(lambda x: next((a for a, v in assets.items() if v.lower() in x.lower()), None))
    df.dropna(inplace=True)

    df["Long"] = pd.to_numeric(df["Long"], errors="coerce")
    df["Short"] = pd.to_numeric(df["Short"], errors="coerce")
    df.dropna(inplace=True)

    df = df.sort_values("As of Date in Form YYYY-MM-DD", ascending=False)
    df = df.drop_duplicates(subset=["Asset"], keep="first")

    df["Long %"] = (df["Long"] / (df["Long"] + df["Short"])) * 100
    df["Short %"] = 100 - df["Long %"]

    return df.sort_values(by="Long %")

# Get data
df = get_cot_data()

# Asset filter
selected_assets = st.multiselect(
    "Select assets to view:",
    options=list(assets.keys()),
    format_func=lambda x: display_names.get(x, x),
    default=[]
)

filtered_df = df[df["Asset"].isin(selected_assets)] if selected_assets else df

# Plot
fig = go.Figure()
fig.add_trace(go.Bar(x=filtered_df["Asset"], y=filtered_df["Long %"], name="Long", marker_color="blue"))
fig.add_trace(go.Bar(x=filtered_df["Asset"], y=filtered_df["Short %"], name="Short", marker_color="red"))

fig.update_layout(
    barmode="stack",
    title="COT Positions by Asset (2025)",
    xaxis_title="Assets",
    yaxis_title="Percentage",
    template="plotly_dark",
    height=600
)

# Show chart
st.plotly_chart(fig, use_container_width=True)

# Format asset names
filtered_df_display = filtered_df.copy().reset_index(drop=True)
filtered_df_display["Asset"] = filtered_df_display["Asset"].apply(lambda x: display_names.get(x, x))

# Show data table
st.markdown("### 📋 Raw COT Data")
st.dataframe(filtered_df_display, use_container_width=True)
