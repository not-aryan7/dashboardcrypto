## Overview

Streamlit-based crypto dashboard with:
- **Market Pulse**: price trajectories, normalization toggle, correlation/vol views.
- **Portfolio Vault**: user-set weights, BTC benchmark, CAGR/Sharpe/Max DD/Vol, equity + drawdown + rolling vol.
- **Alert Studio**: volatility spike, BTC correlation break, and drawdown exceed alerts with supporting charts.

## Quick start

```bash
# (optional) create a virtualenv
python3 -m venv .venv
source .venv/bin/activate

# install deps
pip install -r requirements.txt

# run
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Open the forwarded/local URL (default http://localhost:8501) and navigate pages from the sidebar.
