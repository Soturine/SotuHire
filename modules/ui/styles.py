"""Consistent visual styling for the Streamlit application."""

from __future__ import annotations

import streamlit as st


def inject_styles() -> None:
    """Apply the product theme and improve native Streamlit contrast."""
    st.markdown(
        """
        <style>
        :root {
          --bg: #07111f;
          --surface: #0f1b2d;
          --surface-2: #16243a;
          --border: #263852;
          --text: #f4f7fb;
          --muted: #a8b5c7;
          --accent: #ff5a67;
          --accent-2: #7c8cff;
          --success: #39d98a;
          --warning: #ffcc66;
        }
        .stApp, [data-testid="stAppViewContainer"] {
          background:
            radial-gradient(circle at 88% -10%, rgba(124, 140, 255, .24) 0%, transparent 34%),
            radial-gradient(circle at 10% 0%, rgba(255, 90, 103, .10) 0%, transparent 25%),
            var(--bg);
          color: var(--text);
        }
        .block-container { max-width: 1380px; padding-top: .75rem; padding-bottom: 1.5rem; }
        [data-testid="stHeader"] { background: rgba(7, 17, 31, .92); }
        [data-testid="stSidebar"] {
          background: #0a1423;
          border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] * { color: var(--text); }
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, [data-testid="stCaptionContainer"] {
          color: var(--text);
        }
        [data-testid="stCaptionContainer"] p, .muted { color: var(--muted) !important; }
        [data-testid="stWidgetLabel"] p { color: #dbe5f3 !important; font-weight: 650; }
        .stTextInput input, .stTextArea textarea, .stNumberInput input,
        [data-baseweb="select"] > div {
          background: var(--surface-2) !important;
          color: var(--text) !important;
          border-color: var(--border) !important;
        }
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {
          color: #8190a5 !important;
        }
        [data-testid="stFileUploaderDropzone"] {
          background: linear-gradient(145deg, var(--surface), var(--surface-2));
          border: 1px dashed #49617f;
          border-radius: 16px;
          min-height: 8rem;
        }
        [data-testid="stFileUploaderDropzone"] * { color: var(--muted) !important; }
        [data-testid="stFileUploaderDropzone"] button {
          background: var(--surface);
          border-color: var(--border);
          color: var(--text) !important;
        }
        [data-baseweb="popover"], [data-baseweb="menu"] { background: var(--surface-2); }
        [data-baseweb="menu"] * { color: var(--text); }
        .stButton > button, .stDownloadButton > button {
          background: var(--surface-2);
          color: var(--text);
          border-radius: 12px;
          border: 1px solid var(--border);
          min-height: 2.65rem;
          font-weight: 700;
          transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
          transform: translateY(-1px);
          border-color: #5a7090;
        }
        .stButton > button:disabled, .stDownloadButton > button:disabled {
          background: #111d2e !important;
          border-color: #263852 !important;
          color: #6f8097 !important;
          opacity: .78;
        }
        .stButton > button[kind="primary"] {
          background: linear-gradient(115deg, var(--accent), #e83f67);
          border: 0;
          color: white;
          box-shadow: 0 8px 20px rgba(232, 63, 103, .22);
        }
        .stTabs [data-baseweb="tab-list"] {
          gap: .4rem;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: .4rem;
        }
        .stTabs [data-baseweb="tab"] {
          border-radius: 9px;
          min-height: 2.8rem;
          padding: .45rem .85rem;
          color: var(--muted);
          font-weight: 700;
        }
        .stTabs [aria-selected="true"] {
          background: var(--surface-2);
          color: var(--text) !important;
        }
        [data-testid="stMetric"] {
          background: linear-gradient(145deg, var(--surface), var(--surface-2));
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: .85rem 1rem;
        }
        [data-testid="stMetricLabel"] p { color: var(--muted) !important; }
        [data-testid="stMetricValue"] { color: var(--text); }
        [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
          border-color: var(--border) !important;
          border-radius: 14px;
        }
        [data-testid="stAlert"] { border-radius: 12px; }
        .product-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          padding: .35rem 0 .8rem;
          border-bottom: 1px solid var(--border);
          margin-bottom: 1rem;
        }
        .product-header h1 { margin: 0; font-size: 1.85rem; letter-spacing: -.055em; }
        .product-header p { margin: .2rem 0 .45rem; color: var(--muted); font-size: .92rem; }
        .product-badges { display: flex; flex-wrap: wrap; gap: .35rem; }
        .product-badge {
          border: 1px solid #334965;
          background: rgba(22, 36, 58, .78);
          color: #c8d7ea;
          border-radius: 999px;
          padding: .22rem .58rem;
          font-size: .72rem;
          font-weight: 750;
        }
        .version-pill, .chip {
          display: inline-flex;
          align-items: center;
          border: 1px solid var(--border);
          background: var(--surface-2);
          color: #dce7f6;
          border-radius: 999px;
          padding: .28rem .65rem;
          margin: .16rem .2rem .16rem 0;
          font-size: .82rem;
          font-weight: 650;
        }
        .version-pill { color: #ffd3d7; border-color: #6b3341; background: #2a1621; }
        .section-kicker {
          color: #ff8d98;
          font-size: .76rem;
          font-weight: 800;
          letter-spacing: .12em;
          margin-bottom: .2rem;
        }
        .mode-banner {
          display: flex;
          align-items: center;
          gap: .75rem;
          background: linear-gradient(105deg, rgba(124, 140, 255, .18), rgba(255, 90, 103, .08));
          border: 1px solid #3c5070;
          border-radius: 14px;
          padding: .7rem .9rem;
          margin: .2rem 0 1rem;
          color: var(--muted);
        }
        .mode-banner strong { color: var(--text); white-space: nowrap; }
        .data-card {
          background: linear-gradient(145deg, rgba(15, 27, 45, .96), rgba(16, 31, 51, .96));
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: .78rem .9rem;
          margin: .28rem 0;
          min-height: 3.8rem;
          box-shadow: 0 8px 24px rgba(0, 0, 0, .12);
        }
        .data-card strong { color: var(--text); }
        .data-card strong { overflow-wrap: anywhere; }
        .data-card small { color: var(--muted); display: block; margin-bottom: .25rem; }
        .score-note { color: var(--muted); font-size: .82rem; margin-top: -.55rem; }
        hr { border-color: var(--border) !important; }
        @media (max-width: 900px) {
          .product-header { align-items: flex-start; }
          .version-pill { display: none; }
          .mode-banner { align-items: flex-start; flex-direction: column; gap: .2rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
