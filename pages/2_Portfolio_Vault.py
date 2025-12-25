import streamlit as st
import pandas as pd
import plotly.express as px
from utils.providers import DEFAULT_UNIVERSE, get_prices


st.title("🧭 Portfolio Vault")
st.caption("Set weights, compare against BTC, and review risk/return diagnostics.")

with st.sidebar:
    source = st.selectbox("Data source", ["auto", "binance", "coingecko"], index=0)
    universe = st.multiselect("Portfolio tickers", DEFAULT_UNIVERSE, default=DEFAULT_UNIVERSE[:6])
    st.session_state["universe"] = universe
    start = st.date_input("Start", value=pd.to_datetime("2022-01-01"))
    end = st.date_input("End", value=pd.to_datetime("today"))
    roll_win = st.slider("Rolling vol window (days)", min_value=10, max_value=120, value=30, step=5)

tickers = sorted(set(universe + ["BTC-USD"]))
prices = get_prices(tickers, pd.to_datetime(start), pd.to_datetime(end), source=source)

with st.expander("Data debug"):
    st.write("Source:", source)
    st.write("Shape:", prices.shape)
    st.dataframe(prices.tail(10), use_container_width=True)

if prices.empty:
    st.error("No data returned. Switch source or shorten range.")
    st.stop()

# Weight inputs
st.subheader("Portfolio weights")
weight_cols = st.columns(min(3, len(universe)) or 1)
weights = {}
for idx, t in enumerate(universe):
    with weight_cols[idx % len(weight_cols)]:
        weights[t] = st.number_input(f"{t} weight", value=round(1 / len(universe), 2), step=0.05, format="%.4f")

if not weights:
    st.warning("Select at least one ticker to build a portfolio.")
    st.stop()

weights_series = pd.Series(weights)
if weights_series.sum() <= 0:
    st.error("Weights must sum to a positive value.")
    st.stop()

weights_series = weights_series / weights_series.sum()

# Compute returns
aligned = prices[weights_series.index].ffill().dropna()
btc = prices["BTC-USD"].ffill().dropna()
common_index = aligned.index.intersection(btc.index)
aligned = aligned.loc[common_index]
btc = btc.loc[common_index]

if aligned.empty or btc.empty:
    st.error("Not enough overlapping data for selected tickers and BTC benchmark.")
    st.stop()

rets = aligned.pct_change().dropna()
port_rets = rets.dot(weights_series)
btc_rets = btc.pct_change().dropna()
port_curve = (1 + port_rets).cumprod()
btc_curve = (1 + btc_rets.loc[port_curve.index]).cumprod()

def cagr(series: pd.Series) -> float:
    if series.empty:
        return float("nan")
    total = series.iloc[-1]
    years = (series.index[-1] - series.index[0]).days / 365.25
    if years <= 0:
        return float("nan")
    return (total ** (1 / years)) - 1

def sharpe(series: pd.Series) -> float:
    daily_mean = series.mean()
    daily_std = series.std()
    if daily_std == 0 or pd.isna(daily_std):
        return float("nan")
    return (daily_mean * 252**0.5) / daily_std

def max_drawdown(series: pd.Series) -> float:
    if series.empty:
        return float("nan")
    running_max = series.cummax()
    dd = series / running_max - 1
    return dd.min()

def annual_vol(series: pd.Series) -> float:
    return series.std() * (252 ** 0.5)

metrics = {
    "Portfolio": {
        "CAGR": cagr(port_curve),
        "Sharpe": sharpe(port_rets),
        "Max DD": max_drawdown(port_curve),
        "Vol (ann)": annual_vol(port_rets),
    },
    "BTC": {
        "CAGR": cagr(btc_curve),
        "Sharpe": sharpe(btc_rets),
        "Max DD": max_drawdown(btc_curve),
        "Vol (ann)": annual_vol(btc_rets),
    },
}

cards = []
for label, vals in metrics.items():
    cards.append(
        {
            "Label": label,
            "CAGR": f"{vals['CAGR']*100:,.2f}%",
            "Sharpe": f"{vals['Sharpe']:.2f}",
            "Max DD": f"{vals['Max DD']*100:,.2f}%",
            "Vol (ann)": f"{vals['Vol (ann)']*100:,.2f}%",
        }
    )

st.markdown('<div class="cb-card-grid">', unsafe_allow_html=True)
for card in cards:
    st.markdown(
        f"""
        <div class="cb-card">
          <div class="label">{card['Label']}</div>
          <div class="value">CAGR {card['CAGR']}</div>
          <div class="sub">Sharpe {card['Sharpe']} • Max DD {card['Max DD']} • Vol {card['Vol (ann)']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

st.caption("Weights are normalized to sum to 1.")
st.dataframe(weights_series.to_frame("Weight").style.format("{:.2%}"), use_container_width=True)

# Equity + drawdown
curve_df = pd.DataFrame(
    {
        "Portfolio": port_curve * 100,
        "BTC": btc_curve * 100,
    }
)
st.subheader("Equity curve (base = 100)")
st.plotly_chart(px.line(curve_df, labels={"value": "Growth", "index": "Date"}, title=None), use_container_width=True)

dd = curve_df.divide(curve_df.cummax()) - 1
st.subheader("Drawdown")
st.plotly_chart(px.area(dd, labels={"value": "Drawdown", "index": "Date"}, title=None), use_container_width=True)

# Rolling volatility
roll_port = port_rets.rolling(roll_win).std() * (252 ** 0.5) * 100
roll_btc = btc_rets.rolling(roll_win).std() * (252 ** 0.5) * 100
roll_df = pd.DataFrame({"Portfolio": roll_port, "BTC": roll_btc}).dropna()

st.subheader(f"Rolling volatility ({roll_win}d, annualized)")
st.plotly_chart(px.line(roll_df, labels={"value": "Vol %", "index": "Date"}, title=None), use_container_width=True)
