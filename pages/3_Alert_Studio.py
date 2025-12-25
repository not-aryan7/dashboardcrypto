import streamlit as st
import pandas as pd
import plotly.express as px
from utils.providers import DEFAULT_UNIVERSE, get_prices


st.title("🚨 Alert Studio")
st.caption("Track volatility spikes, correlation breaks, and drawdown breaches for your crypto universe.")

with st.sidebar:
    source = st.selectbox("Data source", ["auto", "binance", "coingecko"], index=0)
    universe = st.multiselect("Universe", DEFAULT_UNIVERSE, default=DEFAULT_UNIVERSE[:6])
    st.session_state["universe"] = universe
    start = st.date_input("Start", value=pd.to_datetime("2022-01-01"))
    end = st.date_input("End", value=pd.to_datetime("today"))
    vol_thr = st.slider("Volatility spike when 30D ann. vol exceeds (%)", 20, 250, 120, step=5)
    corr_window = st.slider("Correlation lookback (days)", 10, 120, 30, step=5)
    corr_thr = st.slider("Correlation break when BTC corr falls below", -1.0, 1.0, 0.6, step=0.05)
    dd_thr = st.slider("Drawdown exceeds (%)", 5, 90, 25, step=5)

tickers = sorted(set(universe + ["BTC-USD"]))
prices = get_prices(tickers, pd.to_datetime(start), pd.to_datetime(end), source=source)

with st.expander("Data debug"):
    st.write("Source:", source)
    st.write("Shape:", prices.shape)
    st.dataframe(prices.tail(10), use_container_width=True)

if prices.empty:
    st.error("No data returned. Switch source or shorten range.")
    st.stop()

rets = prices.pct_change().dropna()
if rets.empty:
    st.error("No return series available for alerts.")
    st.stop()

# Volatility spike
vol30 = rets.rolling(30).std() * (252 ** 0.5) * 100
latest_vol = vol30.iloc[-1].dropna()
vol_alerts = latest_vol[latest_vol > vol_thr].sort_values(ascending=False)

# Correlation break vs BTC
if "BTC-USD" in rets.columns:
    window_slice = rets.tail(corr_window)
    corr_to_btc = window_slice.corr().loc[:, "BTC-USD"].drop("BTC-USD", errors="ignore")
    corr_alerts = corr_to_btc[corr_to_btc < corr_thr].sort_values()
else:
    corr_alerts = pd.Series(dtype=float)

# Drawdown exceeds
dd = prices.ffill().div(prices.ffill().cummax()) - 1
latest_dd = dd.iloc[-1].dropna()
dd_alerts = latest_dd[latest_dd <= -dd_thr / 100].sort_values()

alerts = []
if not vol_alerts.empty:
    alerts.append(("Volatility spike", vol_alerts))
if not corr_alerts.empty:
    alerts.append(("Correlation break vs BTC", corr_alerts))
if not dd_alerts.empty:
    alerts.append(("Drawdown exceeds", dd_alerts))

st.subheader("Triggered alerts")
if not alerts:
    st.success("No alerts triggered with the current thresholds.")
else:
    for title, series in alerts:
        st.markdown(f"**{title}**")
        st.dataframe(series.to_frame("Value").style.format("{:.2f}"), use_container_width=True)

st.subheader("Latest snapshot")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Max vol spike", f"{latest_vol.max():.1f}%" if not latest_vol.empty else "--")
with col2:
    low_corr = corr_alerts.min() if not corr_alerts.empty else float("nan")
    st.metric("Lowest BTC corr", f"{low_corr:.2f}" if not pd.isna(low_corr) else "--")
with col3:
    st.metric("Deepest drawdown", f"{latest_dd.min()*100:.1f}%" if not latest_dd.empty else "--")

# Plots
st.subheader("30D annualized volatility")
st.plotly_chart(px.line(vol30, labels={"value": "Vol %", "index": "Date"}, title=None), use_container_width=True)

if "BTC-USD" in rets.columns:
    st.subheader(f"{corr_window}D correlation to BTC")
    st.plotly_chart(
        px.line(
            rets.rolling(corr_window).corr().loc[pd.IndexSlice[:, "BTC-USD"], :].droplevel(1, axis=0),
            labels={"value": "Corr", "index": "Date"},
            title=None,
        ),
        use_container_width=True,
    )

st.subheader("Drawdown (relative to asset peak)")
st.plotly_chart(px.area(dd, labels={"value": "Drawdown", "index": "Date"}, title=None), use_container_width=True)
