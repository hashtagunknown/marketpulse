import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from cot_reports import cot_year
from datetime import datetime
import os
import pickle

st.set_page_config(page_title="COT Report Dashboard", layout="wide")

# Asset mappings
assets = {
    "ZAR": "So African Rand", "GBP": "EURO FX/BRITISH POUND XRATE", "COPPER": "Copper",
    "JPY": "Japanese Yen", "US10T": "ULTRA UST 10Y", "USOil": "Crude Oil",
    "EUR": "Euro", "USD": "USD INDEX", "CAD": "Canadian Dollar", "SILVER": "Silver",
    "CHF": "Swiss Franc", "BTC": "Bitcoin", "Gold": "Gold", "AUD": "Australian Dollar",
    "RUSSELL": "RUSSELL 2000 ANNUAL DIVIDEND", "NZD": "NZ DOLLAR", "NIKKEI": "NIKKEI STOCK AVERAGE YEN DENOM",
    "PLATINUM": "Platinum", "NASDAQ": "NASDAQ-100 Consolidated", "SPX": "S&P 500 Index",
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

# Load COT data (cached to disk for speed)
@st.cache_data
def get_cot_data():
    if os.path.exists("cot_data.pkl"):
        with open("cot_data.pkl", "rb") as f:
            df = pickle.load(f)
    else:
        df_list = []
        for year in range(2006, datetime.now().year + 1):
            try:
                df = cot_year(year, cot_report_type="legacy_fut", store_txt=False)
                df_list.append(df)
            except Exception as e:
                print(f"Failed for {year}: {e}")
        df = pd.concat(df_list, ignore_index=True)
        df["Date"] = pd.to_datetime(df["As of Date in Form YYYY-MM-DD"])
        df = df.rename(columns={
            "Market and Exchange Names": "Asset",
            "Noncommercial Positions-Long (All)": "Long",
            "Noncommercial Positions-Short (All)": "Short"
        })
        df = df[["Date", "Asset", "Long", "Short"]].dropna()
        df["Asset"] = df["Asset"].apply(lambda x: next((a for a, v in assets.items() if v.lower() in x.lower()), None))
        df.dropna(inplace=True)
        df = df.groupby(["Asset", pd.Grouper(key="Date", freq="W")]).sum().reset_index()
        df["Long %"] = (df["Long"] / (df["Long"] + df["Short"])) * 100
        with open("cot_data.pkl", "wb") as f:
            pickle.dump(df, f)
    return df

# Load data
df = get_cot_data()

st.title("📈 Commitments of Traders (COT) Dashboard")

# Sidebar filters (reverted to date input)
with st.sidebar:
    with st.expander("🔧 Filters", expanded=True):
        asset = st.selectbox("Select Asset", options=list(assets.keys()), format_func=lambda x: display_names.get(x, x))
        asset_df = df[df["Asset"] == asset]
        min_date, max_date = asset_df["Date"].min(), asset_df["Date"].max()
        date_range = st.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
        show_theme = st.checkbox("🌙 Dark Mode", value=True)

# Protect against incomplete date_range input
if len(date_range) < 2:
    st.warning("Please select a complete date range.")
    st.stop()

# Apply filter
filtered = asset_df[
    (asset_df["Date"] >= pd.to_datetime(date_range[0])) &
    (asset_df["Date"] <= pd.to_datetime(date_range[1]))
]

# Sidebar date range bounds
min_date, max_date = asset_df["Date"].min(), asset_df["Date"].max()

# Main date range slider (Streamlit UI)
st.markdown("### 📅 Adjust Date Range")
selected_range = st.slider(
    "Select Date Range",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    format="MMM YYYY"
)

# Apply filter based on Streamlit slider
filtered = asset_df[
    (asset_df["Date"] >= pd.to_datetime(selected_range[0])) &
    (asset_df["Date"] <= pd.to_datetime(selected_range[1]))
]

# Plotly chart with the internal rangeslider enabled
fig = go.Figure()

fig.add_trace(go.Bar(x=filtered["Date"], y=filtered["Long"], name="Long", marker_color="blue"))
fig.add_trace(go.Bar(x=filtered["Date"], y=filtered["Short"], name="Short", marker_color="red"))

fig.add_trace(go.Scatter(
    x=filtered["Date"], y=filtered["Long %"],
    mode="lines", line=dict(shape="hv", color="orange", width=3),
    name="Long %", yaxis="y2"
))

fig.add_trace(go.Scatter(
    x=filtered["Date"], y=[50] * len(filtered),
    mode="lines", name="50% Reference",
    line=dict(color="gray", dash="dot"), yaxis="y2", showlegend=False
))

# Chart layout with internal Plotly rangeslider
fig.update_layout(
    barmode="stack",
    title=f"{display_names.get(asset, asset)} - COT Weekly Positions",
    template="plotly_dark" if show_theme else "plotly_white",
    xaxis=dict(
        title="Date",
        type="date",
        range=[selected_range[0], selected_range[1]],
        rangeslider=dict(visible=True)
    ),
    yaxis=dict(title="Positions"),
    yaxis2=dict(
        title="Long %",
        overlaying="y",
        side="right",
        range=[0, 100],
        showgrid=False
    ),
    hovermode="x unified",
    height=600
)

# Show the chart
st.plotly_chart(fig, use_container_width=True)