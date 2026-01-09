import socket
import time
import requests
import streamlit as st

def _dns(host: str) -> str:
    try:
        return socket.gethostbyname(host)
    except Exception as e:
        return f"DNS FAIL: {e}"

def _http(url: str, timeout: int = 12) -> str:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        return f"{r.status_code} {r.reason}"
    except Exception as e:
        return f"HTTP FAIL: {type(e).__name__}: {e}"

def sidebar_diagnostics(source: str, universe, start: str, end: str):
    with st.sidebar.expander("🧪 Diagnostics", expanded=False):
        st.write("**Inputs**")
        st.write({"source": source, "universe": universe, "start": start, "end": end})

        st.write("**DNS**")
        st.write({
            "api.coingecko.com": _dns("api.coingecko.com"),
            "api.binance.com": _dns("api.binance.com"),
        })

        st.write("**HTTP**")
        st.write({
            "CoinGecko ping": _http("https://api.coingecko.com/api/v3/ping"),
            "Binance ping": _http("https://api.binance.com/api/v3/ping"),
        })

        if st.session_state.get("last_fetch_error"):
            st.error("Last fetch error:")
            st.code(st.session_state["last_fetch_error"])

        if st.button("Clear Data Cache"):
            st.cache_data.clear()
            st.rerun()

        st.caption("If DNS works but HTTP fails, Streamlit Cloud/network is blocking outbound requests or rate limiting you.")
