import streamlit as st


def inject_css():
    st.markdown(
        """
        <style>
          :root {
            --cb-bg: radial-gradient(circle at 20% 20%, rgba(0,255,135,0.18), transparent 25%),
                     radial-gradient(circle at 80% 0%, rgba(0,180,255,0.16), transparent 20%),
                     #0f172a;
            --cb-surface: rgba(255,255,255,0.03);
            --cb-border: 1px solid rgba(255,255,255,0.08);
            --cb-radius: 16px;
          }
          .stApp { background: var(--cb-bg); }
          .block-container { padding-top: 1.2rem; padding-bottom: 2.4rem; }

          .cb-hero {
            display:flex; gap:1.5rem; padding:1.25rem 1.5rem; border-radius:24px;
            border: var(--cb-border); background: linear-gradient(135deg, rgba(34,197,94,0.12), rgba(59,130,246,0.06));
            box-shadow: 0 18px 40px rgba(0,0,0,0.35);
          }
          .cb-hero h1 { margin:0; font-size:1.8rem; font-weight:900; letter-spacing:0.4px; }
          .cb-hero p { opacity:0.82; margin:0.2rem 0 0.8rem 0; font-size:1.05rem; }
          .cb-badges { display:flex; gap:0.45rem; flex-wrap:wrap; }
          .cb-badge { padding:0.35rem 0.7rem; border-radius:20px; border: var(--cb-border); background: rgba(255,255,255,0.08); font-size:0.85rem; }
          .cb-actions { display:flex; gap:0.6rem; align-items:center; flex-wrap:wrap; }
          .cb-btn {
            display:inline-flex; gap:0.4rem; align-items:center;
            padding:0.6rem 0.9rem; border-radius:12px; font-weight:700;
            border: var(--cb-border); text-decoration:none; color:inherit;
            background: rgba(255,255,255,0.08);
            transition: transform 120ms ease, border-color 120ms ease;
          }
          .cb-btn.primary { background: linear-gradient(120deg, #22c55e, #10b981); color:#041b0f; }
          .cb-btn:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.16); }

          .cb-panel {
            padding:1rem 1.1rem; border-radius: var(--cb-radius);
            border: var(--cb-border); background: var(--cb-surface);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
          }
          .cb-panel h3 { margin-top:0; }
          .cb-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:1rem; }
          .cb-phase { padding:1rem; border-radius: var(--cb-radius); border: var(--cb-border); background: rgba(59,130,246,0.05); }
          .cb-phase .label { opacity:0.8; font-size:0.85rem; }
          .cb-phase h4 { margin:0.35rem 0; }
          .cb-phase .desc { opacity:0.82; font-size:0.94rem; }

          .cb-tape { display:flex; gap:0.6rem; flex-wrap:wrap; margin:0.4rem 0 0; }
          .cb-chip {
            display:inline-flex; gap:0.3rem; align-items:center;
            padding:0.35rem 0.6rem; border-radius:12px;
            border: var(--cb-border); background: rgba(255,255,255,0.06);
            font-size:0.9rem; letter-spacing:0.1px;
          }
          .cb-pos { color:#34d399; }
          .cb-neg { color:#f87171; }

          .cb-card-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:0.9rem; }
          .cb-card { padding:0.9rem; border-radius:var(--cb-radius); border: var(--cb-border); background: rgba(255,255,255,0.04); }
          .cb-card .label { opacity:0.8; font-size:0.9rem; }
          .cb-card .value { font-size:1.4rem; font-weight:800; margin-top:0.25rem; }
          .cb-card .sub { opacity:0.72; font-size:0.9rem; margin-top:0.15rem; }

          .css-1dp5vir, .css-zt5igj { border: var(--cb-border) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
