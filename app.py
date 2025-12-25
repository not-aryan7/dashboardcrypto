import streamlit as st
import pandas as pd
from utils.style import inject_css
from utils.providers import DEFAULT_UNIVERSE, get_prices, last_price_and_change

st.set_page_config(page_title="Himalayan Crypto Desk", page_icon="🟦", layout="wide")
inject_css()

universe = st.session_state.get("universe", DEFAULT_UNIVERSE[:6])
today = pd.Timestamp.today()
prices = get_prices(universe, today - pd.Timedelta(days=30), today, source="auto")

with st.container():
    st.markdown(
        """
        <div class="cb-hero">
          <div style="flex:1">
            <div class="cb-badges">
              <span class="cb-badge">Realtime-ready</span>
              <span class="cb-badge">Multi-source data</span>
              <span class="cb-badge">Built for operators</span>
            </div>
            <h1>Himalayan Crypto Desk</h1>
            <p>Monitor markets, inspect portfolios, set goals, and trigger alerts without changing your data workflow.</p>
            <div class="cb-actions">
              <a class="cb-btn primary" href="#workflow">See phases</a>
              <a class="cb-btn" href="/Market_Watch">Open Market Watch</a>
            </div>
          </div>
          <div style="min-width:240px; align-self:center;" class="cb-panel">
            <h3 style="margin-top:0;">Live tape</h3>
            <div class="cb-tape">
        """,
        unsafe_allow_html=True,
    )

    chips = []
    if prices is not None and not prices.empty:
        for t in universe:
            if t in prices.columns:
                px, chg = last_price_and_change(prices[t])
                cls = "cb-pos" if chg >= 0 else "cb-neg"
                chips.append(
                    f'<span class="cb-chip"><b>{t}</b> <span>{px:,.2f}</span> <span class="{cls}">{chg:+.2f}%</span></span>'
                )
    st.markdown("".join(chips) if chips else "No tape data yet (open Market Watch).", unsafe_allow_html=True)

    st.markdown("</div></div></div>", unsafe_allow_html=True)

st.markdown("---")

st.markdown('<div id="workflow"></div>', unsafe_allow_html=True)
st.subheader("Phase-driven workspace")
st.caption("Swap between phases without changing your data model. The features mirror the original dashboard; the layout highlights each phase.")

phases = [
    ("Market Pulse", "Live pricing, microstructure-aware views, and correlation maps for your universe.", "🟢", "/Market_Watch"),
    ("Portfolio Vault", "Track holdings, weights, and drift across time with the same pricing sources.", "🧭", "/2_Portfolio_Vault"),
    ("Alert Studio", "Operational alerts on volatility spikes, correlation breaks, and drawdown breaches.", "🚨", "/3_Alert_Studio"),
]

cols = st.columns(2)
for idx, (title, desc, icon, link) in enumerate(phases):
    with cols[idx % 2]:
        st.markdown(
            f"""
            <div class="cb-phase">
              <div class="label">{icon} Phase {idx+1}</div>
              <h4>{title}</h4>
              <div class="desc">{desc}</div>
              <div style="margin-top:0.7rem;">
                <a class="cb-btn" href="{link}">Launch</a>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

st.subheader("Snapshot")
st.caption("Key pulses for the chosen universe.")

if prices is None or prices.empty:
    st.warning("No data loaded yet. Open Market Watch to pull fresh prices.")
else:
    latest = prices.ffill().iloc[-1]
    base = prices.ffill().iloc[0]
    change = (latest / base - 1).replace([pd.NA, pd.NaT], 0) * 100
    best = change.dropna().sort_values(ascending=False).head(1)
    worst = change.dropna().sort_values().head(1)

    rets = prices.pct_change().dropna(how="all")
    vol = rets.std() * (365 ** 0.5) * 100
    vol_best = vol.sort_values(ascending=False).head(1)

    cards = [
        ("Assets tracked", f"{latest.count()}", "Universe elements currently in view."),
        ("Avg. 30d change", f"{change.mean():+.2f}%", "Equal-weight average across visible tickers."),
        ("Top mover", f"{best.index[0] if not best.empty else '--'} {best.iloc[0]:+.2f}%", "Best 30d delta."),
        ("Vol surface", f"{vol_best.index[0] if not vol_best.empty else '--'} {vol_best.iloc[0]:.1f}%", "Highest annualized vol in range."),
    ]

    st.markdown('<div class="cb-card-grid">', unsafe_allow_html=True)
    for title, value, sub in cards:
        st.markdown(
            f"""
            <div class="cb-card">
              <div class="label">{title}</div>
              <div class="value">{value}</div>
              <div class="sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.caption("Latest closes and short-range change")
    table_rows = []
    for t in universe:
        if t in prices.columns:
            px, chg = last_price_and_change(prices[t])
            table_rows.append({"Ticker": t, "Last": px, "1d %": chg})
    if table_rows:
        st.dataframe(pd.DataFrame(table_rows).set_index("Ticker"), use_container_width=True)

st.info("Tip: open the sidebar inside Market Watch to pivot the universe and sources.")
