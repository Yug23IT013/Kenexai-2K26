# components/chatbot.py
import os
import re
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── QUICK SQL SHORTCUTS ──────────────────────────────────────────
# Maps natural-language phrases the coach might type
# to safe, pre-built SQL queries.
QUICK_QUERIES = {
    "show all high risk players": """
        SELECT po.player_name, ti.team_long_name,
               ROUND(po.injury_risk_prob * 100, 1) AS risk_pct,
               po.injury_risk_label
        FROM predictions_output po
        JOIN player_injury pi ON po.player_id = pi.player_id
        JOIN team_info     ti ON pi.team_id   = ti.team_id
        WHERE po.injury_risk_label = 'High'
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY po.player_id ORDER BY po.predicted_at DESC
        ) = 1
        ORDER BY risk_pct DESC
    """,

    "show all players": """
        SELECT po.player_name, ti.team_long_name,
               po.performance_score,
               po.injury_risk_label,
               ROUND(po.injury_risk_prob * 100, 1) AS risk_pct
        FROM predictions_output po
        JOIN player_injury pi ON po.player_id = pi.player_id
        JOIN team_info     ti ON pi.team_id   = ti.team_id
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY po.player_id ORDER BY po.predicted_at DESC
        ) = 1
        ORDER BY po.performance_score DESC
    """,

    "top performers": """
        SELECT player_name, performance_score, injury_risk_label
        FROM predictions_output
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY player_id ORDER BY predicted_at DESC
        ) = 1
        ORDER BY performance_score DESC
        LIMIT 10
    """,

    "team overview": """
        SELECT ti.team_long_name,
               COUNT(DISTINCT ps.player_id) AS players,
               ROUND(AVG(po.performance_score), 1) AS avg_score,
               SUM(CASE WHEN po.injury_risk_label = 'High' THEN 1 ELSE 0 END) AS high_risk
        FROM player_stats ps
        JOIN team_info ti ON ps.team_id = ti.team_id
        LEFT JOIN predictions_output po ON ps.player_id = po.player_id
        GROUP BY ti.team_long_name
    """,

    "high fatigue players": """
        SELECT pi.player_name, ti.team_long_name,
               pi.fatigue_index, pi.training_load, pi.minutes_played
        FROM player_injury pi
        JOIN team_info ti ON pi.team_id = ti.team_id
        WHERE pi.fatigue_index > 70
        ORDER BY pi.fatigue_index DESC
    """,

    "players with previous injury": """
        SELECT pi.player_name, ti.team_long_name,
               pi.fatigue_index, pi.recovery_time,
               po.injury_risk_label
        FROM player_injury pi
        JOIN team_info ti ON pi.team_id = ti.team_id
        LEFT JOIN predictions_output po ON pi.player_id = po.player_id
        WHERE pi.previous_injury = 1
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY po.player_id ORDER BY po.predicted_at DESC
        ) = 1
    """,
}


def _match_quick_query(user_input: str):
    """Check if the user's message matches a quick query shortcut."""
    text = user_input.lower().strip()
    for phrase, sql in QUICK_QUERIES.items():
        if phrase in text:
            return sql
    return None


def _build_sql_prompt(user_message: str) -> str:
    return f"""
You are a sports analytics SQL assistant. Convert the coach's question into a
valid Snowflake SQL query using ONLY these tables and columns:

Tables:
- player_injury(player_id, player_name, team_id, potential, ball_control,
  dribbling, stamina, reactions, balance, strength, acceleration, age,
  attacking_work_rate_encoded, defensive_work_rate_encoded,
  fatigue_index, matches_last_7_days, minutes_played, recovery_time,
  previous_injury, training_load, injury_risk)

- player_stats(player_id, player_name, team_id, potential, ball_control,
  dribbling, stamina, reactions, balance, strength, acceleration, age,
  attacking_work_rate_encoded, defensive_work_rate_encoded, injury_risk)

- team_stats(team_id, team_long_name, team_short_name, buildUpPlaySpeed,
  buildUpPlayDribbling, buildUpPlayPassing, chanceCreationPassing,
  chanceCreationCrossing, chanceCreationShooting,
  defencePressure, defenceAggression, defenceTeamWidth)

- team_info(team_id, team_long_name, team_short_name)

- predictions_output(pred_id, player_id, player_name, predicted_at,
  performance_score, injury_risk_label, injury_risk_prob, recommendation)

Rules:
- Return ONLY the SQL query, no explanation, no markdown code fences.
- For latest predictions use:
  QUALIFY ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY predicted_at DESC) = 1
- Always join with team_info to get team_long_name when showing team names.
- Limit results to 50 rows max unless user specifies otherwise.

Coach question: {user_message}
SQL:
""".strip()


def _call_openai_for_sql(user_message: str) -> str:
    """Use OpenAI to convert natural language to SQL."""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a Snowflake SQL expert for sports analytics."},
            {"role": "user",   "content": _build_sql_prompt(user_message)},
        ],
        max_tokens=400,
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()
    # Strip any accidental markdown fences
    sql = re.sub(r"```sql|```", "", sql).strip()
    return sql


def _safe_sql(sql: str) -> bool:
    """Block destructive SQL from the chatbot."""
    blocked = ["DROP", "DELETE", "TRUNCATE", "INSERT", "UPDATE", "ALTER", "CREATE"]
    upper   = sql.upper()
    return not any(word in upper for word in blocked)


def render_chatbot():
    """
    Renders the full coach chatbot UI inside a Streamlit page.
    Maintains conversation history in st.session_state.
    """
    from utils.snowflake_queries import run_custom_query

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))

    # Display chat history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "dataframe" in msg:
                st.dataframe(msg["dataframe"], use_container_width=True)

    # Quick query buttons
    st.markdown("**Quick queries:**")
    cols = st.columns(3)
    quick_labels = [
        "Show all high risk players",
        "Top performers",
        "High fatigue players",
    ]
    quick_keys = [
        "show all high risk players",
        "top performers",
        "high fatigue players",
    ]
    for i, (label, key) in enumerate(zip(quick_labels, quick_keys)):
        if cols[i].button(label, use_container_width=True):
            st.session_state["pending_quick"] = key

    # Handle quick query button clicks
    if "pending_quick" in st.session_state:
        user_input = st.session_state.pop("pending_quick")
        _handle_message(user_input, run_custom_query, USE_OPENAI)
        st.rerun()

    # Chat input
    user_input = st.chat_input("Ask about any player or team...")
    if user_input:
        _handle_message(user_input, run_custom_query, USE_OPENAI)
        st.rerun()


def _handle_message(user_input: str, run_query_fn, use_openai: bool):
    """Process a message and generate a response."""
    st.session_state["chat_history"].append({
        "role": "user",
        "content": user_input,
    })

    sql = _match_quick_query(user_input)

    if sql is None and use_openai:
        try:
            sql = _call_openai_for_sql(user_input)
        except Exception as e:
            st.session_state["chat_history"].append({
                "role": "assistant",
                "content": f"Could not generate SQL: {e}. Try a quick query button above.",
            })
            return
    elif sql is None:
        # No OpenAI — suggest quick queries
        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": (
                "I don't have an OpenAI key to parse free-form questions. "
                "Try one of the quick query buttons above, or type one of: "
                + ", ".join(f'"{k}"' for k in QUICK_QUERIES.keys())
            ),
        })
        return

    if not _safe_sql(sql):
        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": "That query is not allowed for safety reasons.",
        })
        return

    try:
        df = run_query_fn(sql)
        st.session_state["chat_history"].append({
            "role":      "assistant",
            "content":   f"Here are the results ({len(df)} rows):",
            "dataframe": df,
        })
    except Exception as e:
        st.session_state["chat_history"].append({
            "role":    "assistant",
            "content": f"Query error: {e}",
        })