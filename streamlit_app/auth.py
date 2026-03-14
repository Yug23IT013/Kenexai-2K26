# auth.py
import streamlit as st

# ── USER REGISTRY ───────────────────────────────────────────────
# In production replace this with a proper DB users table
# Format: username -> { password, role, player_id (None for coaches) }

USERS = {
    # Coaches
    "coach_pep":     {"password": "coach123", "role": "coach",  "player_id": None, "name": "Pep Guardiola"},
    "coach_carlo":   {"password": "coach456", "role": "coach",  "player_id": None, "name": "Carlo Ancelotti"},

    # Players — player_id must match player_id in your Snowflake tables
    "de_bruyne":     {"password": "player123", "role": "player", "player_id": 1,   "name": "Kevin De Bruyne"},
    "pedri":         {"password": "player456", "role": "player", "player_id": 2,   "name": "Pedri"},
    "vinicius":      {"password": "player789", "role": "player", "player_id": 3,   "name": "Vinicius Jr"},
    "haaland":       {"password": "player321", "role": "player", "player_id": 4,   "name": "Erling Haaland"},
}


def login_ui():
    """Renders the login form and handles authentication."""
    st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1rem'>
            <h1 style='font-size:2rem; font-weight:600'>Athlete Analytics Platform</h1>
            <p style='color:gray'>Sign in to your dashboard</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            user = USERS.get(username)
            if user and user["password"] == password:
                st.session_state["logged_in"]  = True
                st.session_state["username"]   = username
                st.session_state["role"]       = user["role"]
                st.session_state["player_id"]  = user["player_id"]
                st.session_state["name"]       = user["name"]
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("---")
        st.markdown(
            "<p style='text-align:center;font-size:12px;color:gray'>"
            "Demo logins — Coach: <b>coach_pep / coach123</b> | "
            "Player: <b>de_bruyne / player123</b></p>",
            unsafe_allow_html=True
        )


def logout():
    for key in ["logged_in", "username", "role", "player_id", "name"]:
        st.session_state.pop(key, None)
    st.rerun()


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def get_role() -> str:
    return st.session_state.get("role", "")


def get_player_id() -> int:
    return st.session_state.get("player_id")


def get_name() -> str:
    return st.session_state.get("name", "User")