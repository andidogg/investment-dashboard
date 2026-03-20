import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
def calculate_rsi(close_prices, period=14):
    """Simple manual RSI calculation (no extra packages needed)"""
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
st.set_page_config(page_title="SmokeDoggyDogg Live Dashboard", layout="wide", page_icon="📈")
# ====================== PASSWORD PROTECTION ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    st.title("🚀 SmokeDoggyDogg's Private Investment Dashboard")
    st.caption("Market data via Yahoo Finance • Secure access required")
    pw = st.text_input("🔒 Enter Password", type="password", key="pw")
    if st.button("Unlock Dashboard"):
        if pw == st.secrets["auth"]["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Wrong password")
    st.stop()

if not st.session_state.authenticated:
    check_password()
# ============================================================
st.title("🚀 SmokeDoggyDogg's Very Detailed Live Investment Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Market data via Yahoo Finance")

# ====================== SIDEBAR ======================
st.sidebar.header("⚙️ Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh every 60 seconds", value=True)
refresh_btn = st.sidebar.button("🔄 Manual Refresh Now")

if refresh_btn or 'data_fetched' not in st.session_state:
    st.session_state.data_fetched = True

# ====================== SESSION STATE ======================
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=['Ticker', 'Shares', 'Avg Cost'])
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META", "BTC-USD"]

# ====================== TABS ======================
tab_overview, tab_watchlist, tab_portfolio, tab_analyzer, tab_news = st.tabs(["📊 Overview", "👀 Watchlist", "💼 Portfolio", "📈 Analyzer", "📰 News"])

# ====================== OVERVIEW TAB ======================
with tab_overview:
    st.subheader("Major Indices")
    indices = ["^GSPC", "^DJI", "^IXIC", "^VIX"]
    cols = st.columns(4)
    for i, idx in enumerate(indices):
        ticker = get_stock_info(idx)
        info = ticker.info
        price = info.get('regularMarketPrice') or info.get('previousClose')
        change_pct = info.get('regularMarketChangePercent', 0)
        color = "green" if change_pct >= 0 else "red"
        with cols[i]:
            st.metric(
                label=idx.replace("^", ""),
                value=f"{price:,.2f}" if price else "N/A",
                delta=f"{change_pct:+.2f}%"
            )

    # Top movers (sample popular stocks)
    st.subheader("🔥 Top Movers Today")
    movers = ["AAPL", "NVDA", "TSLA", "AMD", "AMZN"]
    data = []
    for t in movers:
        tk = get_stock_info(t)
        info = tk.info
        data.append({
            "Ticker": t,
            "Price": info.get('regularMarketPrice') or info.get('previousClose'),
            "Change %": info.get('regularMarketChangePercent', 0)
        })
    df_movers = pd.DataFrame(data)
    st.dataframe(df_movers.style.format({"Price": "${:,.2f}", "Change %": "{:+.2f}%"}), use_container_width=True)

# ====================== WATCHLIST TAB ======================
with tab_watchlist:
    st.subheader("Your Watchlist")
    new_ticker = st.text_input("Add ticker (e.g. GOOGL or BTC-USD)", "")
    if st.button("Add to Watchlist") and new_ticker:
        if new_ticker.upper() not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_ticker.upper())
    
    # Live watchlist table
    watch_data = []
    for t in st.session_state.watchlist:
        info = get_stock_info(t)
        price = info.get('regularMarketPrice') or info.get('previousClose', 0)
        change = info.get('regularMarketChangePercent', 0)
        volume = info.get('regularMarketVolume', 0)
        watch_data.append([t, price, change, volume])
    
    df_watch = pd.DataFrame(watch_data, columns=["Ticker", "Price", "Change %", "Volume"])
    st.dataframe(
        df_watch.style.format({"Price": "${:,.2f}", "Change %": "{:+.2f}%", "Volume": "{:,.0f}"}),
        use_container_width=True
    )
    # ====================== PORTFOLIO TAB ======================
with tab_portfolio:
    st.subheader("Portfolio Tracker")
    
    # Add holding form
    col1, col2, col3, col4 = st.columns([2,1,1,1])
    with col1:
        ticker_add = st.text_input("Ticker", value="AAPL", key="add_ticker")
    with col2:
        shares_add = st.number_input("Shares", min_value=0.01, value=10.0, key="add_shares")
    with col3:
        cost_add = st.number_input("Avg Cost Basis $", min_value=0.01, value=150.0, key="add_cost")
    with col4:
        if st.button("Add Holding"):
            new_row = pd.DataFrame([[ticker_add.upper(), shares_add, cost_add]], columns=['Ticker', 'Shares', 'Avg Cost'])
            st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_row], ignore_index=True)
    
    if not st.session_state.portfolio.empty:
        # Enrich with live data
        portfolio_enriched = st.session_state.portfolio.copy()
        current_values = []
        total_value = 0
        total_cost = 0
        
        for i, row in portfolio_enriched.iterrows():
                        info = get_stock_info(row['Ticker'])
            current_price = info.get('regularMarketPrice') or info.get('previousClose', row['Avg Cost'])
        
        st.dataframe(portfolio_enriched.style.format({
            "Current Price": "${:,.2f}",
            "Market Value": "${:,.2f}",
            "P&L $": "${:,.2f}",
            "P&L %": "{:+.2f}%"
        }), use_container_width=True)
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total Portfolio Value", f"${total_value:,.2f}", f"{((total_value-total_cost)/total_cost*100 if total_cost else 0):+.2f}%")
        col_b.metric("Total Unrealized P&L", f"${total_value - total_cost:,.2f}")
        
        # Allocation pie
        fig_pie = go.Figure(data=[go.Pie(labels=portfolio_enriched['Ticker'], values=portfolio_enriched['Market Value'])])
        st.plotly_chart(fig_pie, use_container_width=True)

# ====================== ANALYZER TAB ======================
with tab_analyzer:
    st.subheader("Deep Stock Analyzer")
    selected = st.selectbox("Choose ticker to analyze", options=st.session_state.watchlist + ["AAPL", "NVDA", "TSLA"], index=0)
    
    ticker_obj = yf.Ticker(selected)
        info = get_stock_info(selected)
    hist = get_stock_history(selected)
    # Candlestick + indicators
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.2, 0.3], vertical_spacing=0.05)
    
    # Candlestick
    fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
    
    # SMA/EMA
    hist['SMA50'] = hist['Close'].rolling(50).mean()
    hist['EMA20'] = hist['Close'].ewm(span=20).mean()
    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="SMA 50", line=dict(color="orange")), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist['EMA20'], name="EMA 20", line=dict(color="blue")), row=1, col=1)
    
    # RSI
    rsi = calculate_rsi(hist['Close'])
    fig.add_trace(go.Scatter(x=hist.index, y=rsi, name="RSI 14", line=dict(color="purple")), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", row=2, col=1, line_color="red")
    fig.add_hline(y=30, line_dash="dash", row=2, col=1, line_color="green")
    
    # Volume
    fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name="Volume", marker_color="gray"), row=3, col=1)
    
    fig.update_layout(height=800, title=f"{selected} - 6 Month Analysis", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Fundamentals
    st.subheader("Key Fundamentals")
    info = ticker_obj.info
    cols_f = st.columns(3)
    cols_f[0].metric("Market Cap", f"${info.get('marketCap', 0)/1e9:.1f}B")
    cols_f[1].metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
    cols_f[2].metric("52-Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A'):.2f}")

# ====================== NEWS TAB ======================
with tab_news:
    st.subheader("Latest News")
    news = ticker_obj.news[:10] if hasattr(ticker_obj, 'news') else []
    for item in news:
        st.markdown(f"**{item.get('title')}**  \n{item.get('publisher')} | {datetime.fromtimestamp(item.get('providerPublishTime', 0))}")
        st.markdown(item.get('link', ''))
        st.divider()

# ====================== AUTO REFRESH ======================


st.sidebar.success("Dashboard running live! Edit watchlist/portfolio anytime.")
