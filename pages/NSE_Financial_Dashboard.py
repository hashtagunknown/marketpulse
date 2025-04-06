import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import streamlit.components.v1 as components

# Configure layout
st.set_page_config(layout="wide")
st.title("📈 NSE Financial Dashboard")


st.title("📈 Market Overview")

# Embed TradingView Ticker Tape Widget
components.html(
    """
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {
      "symbols": [
        {
          "proName": "FOREXCOM:SPXUSD",
          "title": "S&P 500 Index"
        },
        {
          "proName": "FOREXCOM:NSXUSD",
          "title": "US 100 Cash CFD"
        },
        {
          "proName": "FX_IDC:EURUSD",
          "title": "EUR to USD"
        },
        {
          "proName": "BITSTAMP:BTCUSD",
          "title": "Bitcoin"
        },
        {
          "proName": "BITSTAMP:ETHUSD",
          "title": "Ethereum"
        }
      ],
      "showSymbolLogo": true,
      "isTransparent": false,
      "displayMode": "adaptive",
      "colorTheme": "dark",
      "locale": "en"
    }
      </script>
    </div>
    <!-- TradingView Widget END -->
    """,
    height=90
)

# Function to fetch stock data
def fetch_stock_data(ticker, period):
    try:
        stock = yf.Ticker(f"{ticker}.NS")  # Ensure .NS suffix
        info = stock.info
        history = stock.history(period=period)
        return history, info
    except Exception as e:
        st.error(f"⚠ Error fetching data for {ticker}.NS: {e}")
        return pd.DataFrame(), {}

# Function to calculate Simple Moving Average (SMA)
def calculate_sma(data, window):
    return data['Close'].rolling(window=window).mean()

# Function to calculate Exponential Moving Average (EMA)
def calculate_ema(data, window):
    return data['Close'].ewm(span=window, adjust=False).mean()

# Sidebar: Select Aspect
# Sidebar: Select Aspect
tab_names = ['Equity Market', 'Market Indices', 'Correlation', 'Volatility Analysis', 'Market News']
selected_index = tab_names.index(st.sidebar.selectbox("Select Section", tab_names))

instrument_options = ['NSE Equity Market', 'Market Indices', 'Correlation Analysis', 'Volatility Analysis', 'Market News']
instrument = st.session_state.get('instrument', instrument_options[0])

if selected_index == 0:
    instrument = instrument_options[0]
elif selected_index == 1:
    instrument = instrument_options[1]
elif selected_index == 2:
    instrument = instrument_options[2]
elif selected_index == 3:
    instrument = instrument_options[3]
elif selected_index == 4:
    instrument = instrument_options[4]

st.session_state['instrument'] = instrument

# Equity Market Section
if instrument == 'NSE Equity Market':
    st.header('📊 NSE Equity Market')
    ticker = st.sidebar.text_input('Enter Stock Symbol (e.g., SBIN)', '').upper()
    period = st.sidebar.selectbox('Select Time Period', ['1mo', '3mo', '6mo', '1y', '5y'])
    show_indicators = st.sidebar.checkbox('Show Technical Indicators')
    sma_window = st.sidebar.slider('SMA Window', min_value=5, max_value=200, value=20, step=5, disabled=not show_indicators)
    ema_window = st.sidebar.slider('EMA Window', min_value=5, max_value=200, value=50, step=5, disabled=not show_indicators)
    show_volume = st.sidebar.checkbox('Show Volume Chart', value=False)
    show_bollinger = st.sidebar.checkbox('Show Bollinger Bands', value=False)
    bollinger_window = st.sidebar.slider('Bollinger Window', min_value=5, max_value=50, value=20, step=1, disabled=not show_bollinger)
    bollinger_std = st.sidebar.slider('Bollinger Std Dev', min_value=1.0, max_value=3.0, value=2.0, step=0.5, disabled=not show_bollinger)

    if ticker:
        stock_data, stock_info = fetch_stock_data(ticker, period) # Use the ticker as entered

        if not stock_data.empty:
            st.subheader('🔍 Stock Overview')
            st.write(f"*Company Name:* {stock_info.get('longName', 'N/A')}")
            st.write(f"*Market Cap:* {stock_info.get('marketCap', 'N/A')}")
            st.write(f"*P/E Ratio:* {stock_info.get('trailingPE', 'N/A')}")
            st.write(f"*Dividend Yield:* {stock_info.get('dividendYield', 'N/A')}")
            st.write(f"*52-Week High:* {stock_info.get('fiftyTwoWeekHigh', 'N/A')}")
            st.write(f"*52-Week Low:* {stock_info.get('fiftyTwoWeekLow', 'N/A')}")

            st.subheader('📈 Stock Price Trend')
            fig = go.Figure()

            # Price Line
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], name='Close', line=dict(color='blue')))

            # Moving Averages
            if show_indicators:
                stock_data['SMA'] = calculate_sma(stock_data, sma_window)
                stock_data['EMA'] = calculate_ema(stock_data, ema_window)
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['SMA'], line=dict(color='orange'), name=f'SMA ({sma_window})'))
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['EMA'], line=dict(color='purple'), name=f'EMA ({ema_window})'))

            # Bollinger Bands
            if show_bollinger:
                stock_data['Middle Band'] = calculate_sma(stock_data, bollinger_window)
                stock_data['Upper Band'] = stock_data['Middle Band'] + (stock_data['Close'].rolling(window=bollinger_window).std() * bollinger_std)
                stock_data['Lower Band'] = stock_data['Middle Band'] - (stock_data['Close'].rolling(window=bollinger_window).std() * bollinger_std)

                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Upper Band'], line=dict(color='gray', dash='dash'), name=f'Upper Band ({bollinger_window}, {bollinger_std}σ)'))
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Lower Band'], line=dict(color='gray', dash='dash'), name=f'Lower Band ({bollinger_window}, {bollinger_std}σ)'))
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Middle Band'], line=dict(color='lightgray'), name=f'Middle Band ({bollinger_window})'))

            fig.update_layout(title=f"{ticker} Stock Price with Indicators", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)

            if show_volume:
                fig_volume = px.bar(stock_data, x=stock_data.index, y='Volume', title=f"{ticker} Trading Volume")
                st.plotly_chart(fig_volume, use_container_width=True)

            st.subheader('📄 Raw Data')
            st.dataframe(stock_data)
            tradingview_symbol = f"NSE:{ticker}"
            components.html(
                f"""<!-- TradingView Widget BEGIN -->
                <div class="tradingview-widget-container">
                  <div class="tradingview-widget-container__widget"></div>
                  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
                  {{
                    "interval": "1D",
                    "width": "425",
                    "isTransparent": true,
                    "height": "450",
                    "symbol": "{tradingview_symbol}",
                    "showIntervalTabs": true,
                    "displayMode": "single",
                    "locale": "en",
                    "colorTheme": "dark"
                  }}
                  </script>
                </div>
                <!-- TradingView Widget END -->""",
                height=900
            )
        else:
            st.warning(f"⚠ No data available for the stock symbol: {ticker}. Please ensure it is a valid NSE ticker (e.g., SBIN, INFY).")
        
        

# Market Indices Section
elif instrument == "Market Indices":
    st.subheader("📊 NSE Market Indices")
    index = st.sidebar.selectbox("Select Index:", ["NIFTY 50", "SENSEX", "BANKNIFTY"])
    indices_mapping = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "BANKNIFTY": "^NSEBANK"
    }
    ticker = indices_mapping.get(index)

    if ticker:
        period_indices = st.sidebar.selectbox("Select Time Period:", ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'], index=3) # Default to 1y
        stock = yf.Ticker(ticker)
        data = stock.history(period=period_indices)
        st.write(f"### 📊 {index} Performance")

        if not data.empty:
            # Interactive Chart with Zoom and Pan
            fig = go.Figure(data=[go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Closing Price')])
            fig.update_layout(
                title=f"{index} Closing Prices ({period_indices})",
                xaxis_title="Date",
                yaxis_title="Price",
                xaxis_rangeslider_visible=True # Add a range slider for zooming
            )
            st.plotly_chart(fig, use_container_width=True)

            # Display Key Statistics
            st.subheader("Key Statistics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Start Price", f"{data['Close'].iloc[0]:.2f}")
            with col2:
                st.metric("End Price", f"{data['Close'].iloc[-1]:.2f}")
            with col3:
                price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
                percent_change = (price_change / data['Close'].iloc[0]) * 100
                st.metric("Price Change", f"{price_change:.2f}", f"{percent_change:.2f}%")
            with col4:
                if len(data) > 1:
                    daily_returns = data['Close'].pct_change().dropna()
                    if not daily_returns.empty:
                        annualized_volatility = daily_returns.std() * (252**0.5) * 100
                        st.metric("Annualized Volatility", f"{annualized_volatility:.2f}%")
                    else:
                        st.metric("Annualized Volatility", "N/A")
                else:
                    st.metric("Annualized Volatility", "N/A")

            # Display Raw Data with Download Option
            st.subheader("Raw Data")
            st.dataframe(data)
            csv = data.to_csv(index=True)
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name=f"{index.replace(' ', '')}_data{period_indices}.csv",
                mime="text/csv",
            )

        else:
            st.write("⚠ No data available for the selected time period.")
    else:
        st.write("⚠ Index ticker not found.")

# Correlation Analysis Section
elif instrument == 'Correlation Analysis':
    st.header('📉 Correlation Analysis')
    stock_ticker = st.sidebar.text_input('Enter Stock Symbol for Correlation (e.g., RELIANCE)', '').upper()
    index_to_compare = st.sidebar.selectbox('Select Index to Compare With:', ["NIFTY 50", "SENSEX", "BANKNIFTY"])
    correlation_period = st.sidebar.selectbox('Select Time Period for Correlation', ['3mo', '6mo', '1y', '2y'])

    indices_mapping_correlation = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "BANKNIFTY": "^NSEBANK"
    }
    index_ticker = indices_mapping_correlation.get(index_to_compare)

    if stock_ticker and index_ticker:
        try:
            stock_df, _ = fetch_stock_data(stock_ticker, correlation_period) # Use the ticker as entered
            index_df = yf.download(index_ticker, period=correlation_period)

            if stock_df is not None and not stock_df.empty and index_df is not None and not index_df.empty:
                # Make DateTimeIndices timezone-naive
                stock_df.index = stock_df.index.tz_localize(None)
                index_df.index = index_df.index.tz_localize(None)

                st.subheader(f"Stock Data (First 5 Rows - {stock_ticker}):")
                st.dataframe(stock_df.head())
                st.subheader(f"Index Data (First 5 Rows - {index_to_compare}):")
                st.dataframe(index_df.head())

                # Flatten MultiIndex columns of index_df if it exists
                if isinstance(index_df.columns, pd.MultiIndex):
                    index_df.columns = index_df.columns.get_level_values(0)

                # Select only the 'Close' column and rename it before merging
                stock_close = stock_df[['Close']].rename(columns={'Close': f'Close_{stock_ticker}'})
                index_close = index_df[['Close']].rename(columns={'Close': f'Close_{index_to_compare}'})

                # Align the dates and merge
                merged_df = pd.merge(stock_close, index_close, left_index=True, right_index=True, how='inner')

                st.subheader("Merged Data (First 5 Rows):")
                st.dataframe(merged_df.head())

                if f'Close_{stock_ticker}' in merged_df.columns and f'Close_{index_to_compare}' in merged_df.columns:
                    correlation = merged_df[f'Close_{stock_ticker}'].corr(merged_df[f'Close_{index_to_compare}'])

                    st.subheader(f"📊 Correlation between {stock_ticker} and {index_to_compare}")
                    st.write(f"*Correlation Coefficient:* {correlation:.2f}")
                    st.info(f"A correlation coefficient close to 1 indicates a strong positive correlation, -1 a strong negative correlation, and 0 indicates no linear correlation.")

                    # Visualize the price trends together
                    fig_correlation = go.Figure()
                    fig_correlation.add_trace(go.Scatter(x=merged_df.index, y=merged_df[f'Close_{stock_ticker}'], name=stock_ticker, yaxis='y1'))
                    fig_correlation.add_trace(go.Scatter(x=merged_df.index, y=merged_df[f'Close_{index_to_compare}'], name=index_to_compare, yaxis='y2'))

                    fig_correlation.update_layout(
                        title=f"{stock_ticker} vs {index_to_compare} Price Trends",
                        xaxis_title="Date",
                        yaxis=dict(title=stock_ticker, side="left", color="blue"),
                        yaxis2=dict(title=index_to_compare, side="right", overlaying="y", color="red"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_correlation)

                    # Scatter plot to visualize correlation
                    fig_scatter = px.scatter(merged_df, x=f'Close_{stock_ticker}', y=f'Close_{index_to_compare}',
                                              title=f"Scatter Plot: {stock_ticker} vs {index_to_compare}")
                    st.plotly_chart(fig_scatter)

                else:
                    st.error(f"⚠ Still could not find 'Close' columns with suffixes '{stock_ticker}' and '{index_to_compare}' in the merged DataFrame. Inspect the 'Stock Data' and 'Index Data' outputs above.")

            else:
                st.warning(f"⚠ Could not retrieve data for {stock_ticker}.NS or {index_to_compare} for the selected period.")

        except Exception as e:
            st.error(f"⚠ An error occurred during correlation analysis: {e}")



# Volatility Analysis Section
elif instrument == 'Volatility Analysis':
    st.header('🔥 Volatility Analysis')
    ticker_volatility = st.sidebar.text_input('Enter Stock Symbol for Volatility Analysis (e.g., SBIN)', '').upper()
    period_volatility = st.sidebar.selectbox('Select Time Period for Volatility', ['3mo', '6mo', '1y', '2y'])

    if ticker_volatility:
        try:
            stock_data_volatility, _ = fetch_stock_data(ticker_volatility, period_volatility)
            if not stock_data_volatility.empty:
                st.subheader(f"📊 Historical Volatility of {ticker_volatility}")

                # Calculate daily returns
                stock_data_volatility['Daily Returns'] = stock_data_volatility['Close'].pct_change().dropna()

                # Calculate rolling standard deviation (volatility)
                window_volatility = st.sidebar.slider('Rolling Volatility Window (days)', min_value=5, max_value=90, value=20, step=5)
                stock_data_volatility['Volatility'] = stock_data_volatility['Daily Returns'].rolling(window=window_volatility).std() * (252**0.5) * 100  # Annualized

                # Volatility Chart
                fig_volatility = go.Figure()
                fig_volatility.add_trace(go.Scatter(
                    x=stock_data_volatility.index,
                    y=stock_data_volatility['Volatility'],
                    name=f'Volatility ({window_volatility}-day Rolling)',
                    line=dict(color='red')
                ))
                fig_volatility.update_layout(title=f'{ticker_volatility} - Rolling Volatility')
                st.plotly_chart(fig_volatility)

                # Close Price and Bollinger Bands
                st.subheader("📈 Price with Bollinger Bands")
                bb_window = st.sidebar.slider('Bollinger Band Window', min_value=5, max_value=50, value=20)
                bb_std = st.sidebar.slider('Bollinger Std Dev', min_value=1.0, max_value=3.0, value=2.0, step=0.5)
                stock_data_volatility['Middle Band'] = stock_data_volatility['Close'].rolling(window=bb_window).mean()
                stock_data_volatility['Upper Band'] = stock_data_volatility['Middle Band'] + (stock_data_volatility['Close'].rolling(window=bb_window).std() * bb_std)
                stock_data_volatility['Lower Band'] = stock_data_volatility['Middle Band'] - (stock_data_volatility['Close'].rolling(window=bb_window).std() * bb_std)

                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(x=stock_data_volatility.index, y=stock_data_volatility['Close'], name='Close', line=dict(color='blue')))
                fig_price.add_trace(go.Scatter(x=stock_data_volatility.index, y=stock_data_volatility['Upper Band'], name='Upper Band', line=dict(color='gray', dash='dash')))
                fig_price.add_trace(go.Scatter(x=stock_data_volatility.index, y=stock_data_volatility['Lower Band'], name='Lower Band', line=dict(color='gray', dash='dash')))
                fig_price.add_trace(go.Scatter(x=stock_data_volatility.index, y=stock_data_volatility['Middle Band'], name='Middle Band', line=dict(color='lightgray')))
                fig_price.update_layout(title=f"{ticker_volatility} Close Price with Bollinger Bands")
                st.plotly_chart(fig_price)

                # Highlight High Volatility Points
                st.subheader("📍 High Volatility Points")
                vol_threshold = st.sidebar.slider('Volatility Threshold (%)', min_value=10.0, max_value=100.0, value=50.0, step=5.0)
                high_vol_df = stock_data_volatility[stock_data_volatility['Volatility'] > vol_threshold]
                st.write(f"Number of Days with Volatility > {vol_threshold}%: {len(high_vol_df)}")
                st.dataframe(high_vol_df[['Close', 'Volatility']])

                # Download Option
                csv_vol = stock_data_volatility.to_csv(index=True)
                st.download_button(
                    label="Download Volatility Data as CSV",
                    data=csv_vol,
                    file_name=f"{ticker_volatility}_volatility_data.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(f"An error occurred: {e}")


elif instrument == 'Market News':
    components.html(
        """<!-- TradingView Widget BEGIN -->
            <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"></a></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
            {
            "feedMode": "market",
            "market": "stock",
            "isTransparent": true,
            "displayMode": "regular",
            "width": 400,
            "height": 550,
            "colorTheme": "dark",
            "locale": "en"
            }
            </script>
            </div>
            <!-- TradingView Widget END -->""",
            height=800
            )