import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
from fredapi import Fred
from dotenv import load_dotenv
import os
from collections import defaultdict

# Load environment variables
load_dotenv()
FRED_API_KEY = "a9e4dd54b454e8828d8ef26a11dd314d"
if not FRED_API_KEY:
    st.error("FRED API Key not found. Please set it in your .env file.")
    st.stop()

fred = Fred(api_key=FRED_API_KEY)

# Page config
st.set_page_config(page_title="📈 Market Correlation Matrix", layout="wide")
st.title("📈 Market Correlation Heatmap")

# Market selector
market = st.selectbox("Select Market", ["US Market", "Indian Market"])

# Load data functions
@st.cache_data
def load_us_data():
    df = pd.read_pickle("price_data.pkl")
    df.index = pd.to_datetime(df.index)

    # Flatten MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns]
    else:
        df.columns = [str(col).strip() for col in df.columns]

    df = df.loc[:, df.notna().mean() > 0.7]
    return df

@st.cache_data
def load_india_data():
    tickers = {
        "RELIANCE": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "INFY": "INFY.NS",
        "HDFCBANK": "HDFCBANK.NS",
        "ICICIBANK": "ICICIBANK.NS",
        "SBIN": "SBIN.NS",
        "KOTAKBANK": "KOTAKBANK.NS"
    }
    data = yf.download(list(tickers.values()), period="max")["Adj Close"]
    data.columns = list(tickers.keys())
    return data

@st.cache_data
def load_us_macro_data():
    macro = {
        "USInfl_Inflation": fred.get_series("CPIAUCSL"),  # Consumer Price Index
        "USGDP_GDP": fred.get_series("GDP"),             # Gross Domestic Product
        "USBond_10Y_Bond_Rate": fred.get_series("GS10")   # 10-Year Treasury
    }
    df = pd.DataFrame(macro)
    df.index = pd.to_datetime(df.index)
    df = df.resample("D").ffill()  # Daily frequency
    return df

# Load data
if market == "US Market":
    price_df = load_us_data()
    macro_df = load_us_macro_data()
    price_df = price_df.join(macro_df, how="outer")
else:
    price_df = load_india_data()
    macro_df = None  # Not used for India

# Year slider
max_date = price_df.index.max()

# Calculate when at least 70% of assets have non-NaN values
non_nan_counts = price_df.notna().sum(axis=1)
threshold = int(price_df.shape[1] * 0.7)
valid_dates = non_nan_counts[non_nan_counts >= threshold].index

if valid_dates.empty:
    st.error("Not enough valid data to compute correlation.")
    st.stop()

min_date = valid_dates.min()
max_years = max(1, round((max_date - min_date).days / 365.25))


# Ensure max_years is not less than the default value
default_years = min(2, max_years)

years_back = st.slider("Select number of years of data to include",
                       min_value=1,
                       max_value=max_years,
                       value=default_years)
start_date = max_date - pd.DateOffset(years=years_back)

# Filter by date
filtered_df = price_df.loc[start_date:max_date]
st.caption(f"Showing data from **{start_date.date()}** to **{max_date.date()}**")

# Clean display names
def clean_display_names(tickers):
    seen = defaultdict(int)
    display = {}
    for ticker in tickers:
        label = ticker.split("_")[0] if "_" in ticker else ticker
        seen[label] += 1
        if seen[label] > 1:
            label = f"{label}_{seen[label]}"
        display[ticker] = label
    return display

asset_options = sorted([c for c in filtered_df.columns if pd.notna(c)])
display_names = clean_display_names(asset_options)

selected_assets = st.multiselect(
    "Select Assets to Include",
    options=asset_options,
    default=asset_options[:10],
    format_func=lambda x: display_names.get(x, x)
)

if not selected_assets:
    st.warning("Please select at least one asset to continue.")
    st.stop()

# Drop NaNs
drop_nans = st.checkbox("Drop rows with missing values", value=True)
selected_df = filtered_df[selected_assets]
if drop_nans:
    selected_df = selected_df.dropna()

# Daily returns & correlation
returns = selected_df.pct_change().dropna()
if returns.empty or returns.shape[1] < 2:
    st.warning("Not enough data to compute correlation.")
    st.stop()

correlation = returns.corr()
correlation.rename(index=display_names, columns=display_names, inplace=True)

# Plot
fig = px.imshow(
    correlation,
    text_auto=".2f",
    color_continuous_scale="blues",
    zmin=-1,
    zmax=1,
    labels=dict(color="Correlation"),
    title=f"Correlation Matrix of Daily Returns ({start_date.date()} to {max_date.date()})"
)
st.plotly_chart(fig, use_container_width=True)
