# app.py
import streamlit as st
import sys
import os

# Make sure all submodules are importable
sys.path.insert(0, os.path.dirname(__file__))

from auth import login_ui, logout, is_logged_in, get_role, get_player_id, get_name
from pages import player_dashboard, coach_dashboard

# ── PAGE CONFIG ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Athlete Analytics Platform",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── GLOBAL STYLES ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Completely hide sidebar */
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stPageContainer"] > nav { display: none !important; }
    
    /* Full width container with centered content */
    .appview-container {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        width: 100vw !important;
    }
    
    .main {
        max-width: 1400px;
        width: 100%;
        padding: 20px;
        display: flex;
        flex-direction: column;
    }
    
    [data-testid="stAppViewContainer"] {
        display: flex;
        justify-content: center !important;
        width: 100% !important;
    }
    
    /* Metrics styling */
    .stMetric { background: var(--background-color); border-radius: 10px; padding: 12px; }
    div[data-testid="metric-container"] {
        background-color: rgba(240,242,246,0.05);
        border: 1px solid rgba(250,250,250,0.1);
        border-radius: 10px;
        padding: 12px 16px;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 500;
    }
    
    /* Center login form */
    .login-container {
        max-width: 500px;
        margin: 50px auto;
        padding: 40px;
        border-radius: 10px;
        text-align: center;
    }
    
    /* Top right logout button */
    .logout-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 999;
    }
    
    /* Navbar styling - compact and clean */
    [data-testid="stHorizontalBlock"] {
        padding: 0 !important;
        margin: 0 !important;
        gap: 8px !important;
    }
    
    /* Button styling for logout */
    button[data-testid="baseButton-secondary"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        height: 40px !important;
        min-height: 40px !important;
        transition: all 0.2s ease !important;
    }
    
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #FF3333 !important;
        box-shadow: 0 2px 8px rgba(255, 75, 75, 0.3) !important;
    }
    
    /* Reduce column spacing and padding for navbar */
    .row-widget.stHorizontalBlock {
        margin-top: 0 !important;
        margin-bottom: 8px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Compact horizontal blocks */
    [data-testid="stHorizontalBlock"] [data-testid="stColumn"] {
        padding: 0 !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── ROUTING ──────────────────────────────────────────────────────
if not is_logged_in():
    login_ui()
else:
    role = get_role()
    name = get_name()

    # Top-right logout button - compact navbar
    col1, col2 = st.columns([18, 2])
    with col2:
        if st.button("Logout", use_container_width=True):
            logout()
    
    st.markdown("<hr style='margin: 12px 0; border: 0.5px solid rgba(250,250,250,0.1);'>", unsafe_allow_html=True)
    
    # Route to correct dashboard
    if role == "coach":
        coach_dashboard.render(coach_name=name)
    elif role == "player":
        player_dashboard.render(
            player_id=get_player_id(),
            player_name=name,
        )
    else:
        st.error("Unknown role. Please sign out and log in again.")