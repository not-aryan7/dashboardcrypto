import streamlit as st
import pandas as pd
import plotly.express as px
from utils.diagnostics import sidebar_diagnostics
from utils.providers import DEFAULT_UNIVERSE, get_prices

st.title("🟦 Market Pulse")
st.caption("Use Normalized to 100 Chart style for best visualization chart")

with st.sidebar:
    source = st.selectbox("Data source", ["auto", "binance", "coingecko"], index=0)
    universe = st.multiselect("Universe", DEFAULT_UNIVERSE, default=DEFAULT_UNIVERSE[:6])
    st.session_state["universe"] = universe
    start = st.date_input("Start", value=pd.to_datetime("2023-01-01"))
    end = st.date_input("End", value=pd.to_datetime("today"))
    scale = st.radio(
        "Chart scale",
        ["Raw prices", "Normalized to 100 (start date)"],
        index=0,
        help="Normalize divides each series by its first value in the selected window and multiplies by 100.",
    )
    sidebar_diagnostics(source, universe, str(start), str(end))

prices = get_prices(universe, pd.to_datetime(start), pd.to_datetime(end), source=source)

with st.expander("Data debug"):
    st.write("Source:", source)
    st.write("Shape:", prices.shape)
    st.dataframe(prices.tail(10), use_container_width=True)

if prices.empty:
    st.error("No data returned. Switch source or shorten range.")
    st.stop()

latest = prices.ffill().iloc[-1]
base = prices.ffill().iloc[0]
change = (latest / base - 1) * 100
rets = prices.pct_change().dropna(how="all")
vol = rets.std() * (365 ** 0.5) * 100

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown(
        f"""
        <div class="cb-card">
          <div class="label">Active symbols</div>
          <div class="value">{len(prices.columns)}</div>
          <div class="sub">Tracked in this session</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_b:
    st.markdown(
        f"""
        <div class="cb-card">
          <div class="label">Avg. change in window</div>
          <div class="value">{change.mean():+.2f}%</div>
          <div class="sub">Equal-weight move</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_c:
    hottest = change.sort_values(ascending=False)
    st.markdown(
        f"""
        <div class="cb-card">
          <div class="label">Top performer</div>
          <div class="value">{hottest.index[0]} {hottest.iloc[0]:+.2f}%</div>
          <div class="sub">Across selected range</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.subheader("Price trajectory")
if scale.startswith("Normalized"):
    base = prices.ffill().iloc[0]
    display = prices.divide(base).multiply(100)
    y_label = "Indexed to 100 (range start)"
else:
    display = prices
    y_label = "Close (USD)"

st.plotly_chart(px.line(display, title=None, labels={"value": y_label, "index": "Date"}), use_container_width=True)

st.subheader("Risk + co-movement")
col1, col2 = st.columns([1.2, 1])
with col1:
    st.plotly_chart(px.imshow(rets.corr(), text_auto=".2f", aspect="auto", color_continuous_scale="PuBuGn"), use_container_width=True)
with col2:
    vol_table = vol.sort_values(ascending=False).to_frame("Ann. Vol %")
    st.dataframe(vol_table.style.format("{:.1f}"), use_container_width=True, height=320)
