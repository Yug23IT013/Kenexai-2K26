# utils/snowflake_queries.py
import os
import pandas as pd
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

SNOWFLAKE_CONFIG = {
    "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
    "user":      os.getenv("SNOWFLAKE_USER"),
    "password":  os.getenv("SNOWFLAKE_PASSWORD"),
    "database":  os.getenv("SNOWFLAKE_DATABASE",  "sports_db"),
    "schema":    os.getenv("SNOWFLAKE_SCHEMA",     "analytics"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE",  "sports_wh"),
    "role":      os.getenv("SNOWFLAKE_ROLE",       "ACCOUNTADMIN"),
}


@st.cache_resource
def get_engine():
    return create_engine(URL(**SNOWFLAKE_CONFIG))


@st.cache_data(ttl=300)
def get_player_prediction(player_id: int) -> pd.DataFrame:
    """Latest prediction row for a single player."""
    query = f"""
        SELECT
            po.player_id,
            po.player_name,
            ti.team_long_name,
            po.performance_score,
            CASE 
                WHEN po.injury_risk > 0.7 THEN 'High'
                WHEN po.injury_risk > 0.5 THEN 'Medium'
                ELSE 'Low'
            END as injury_risk_label,
            po.injury_risk as injury_risk_prob,
            po.recommendation,
            po.predicted_at
        FROM predictions_output po
        LEFT JOIN player_stats ps ON po.player_id = ps.player_id
        LEFT JOIN team_info     ti ON po.team_id = ti.team_id
        WHERE po.player_id = {player_id}
        ORDER BY po.predicted_at DESC
        LIMIT 1
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=300)
def get_player_stats(player_id: int) -> pd.DataFrame:
    """Full skill stats for a single player."""
    query = f"""
        SELECT
            ps.player_name,
            ps.potential,
            ps.ball_control,
            ps.dribbling,
            ps.stamina,
            ps.reactions,
            ps.balance,
            ps.strength,
            ps.acceleration,
            ps.age,
            ti.team_long_name
        FROM player_stats ps
        JOIN team_info ti ON ps.team_id = ti.team_id
        WHERE ps.player_id = {player_id}
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=300)
def get_player_injury_details(player_id: int) -> pd.DataFrame:
    """Injury feature data for a single player."""
    query = f"""
        SELECT
            fatigue_index,
            matches_last_7_days,
            minutes_played,
            recovery_time,
            previous_injury_count as previous_injury,
            training_load,
            injury_risk
        FROM player_injury
        WHERE player_id = {player_id}
        LIMIT 1
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=300)
def get_all_players_summary() -> pd.DataFrame:
    """Coach view — all players with latest predictions."""
    query = """
        SELECT
            po.player_id,
            po.player_name,
            ti.team_long_name,
            po.performance_score,
            CASE 
                WHEN po.injury_risk > 0.7 THEN 'High'
                WHEN po.injury_risk > 0.5 THEN 'Medium'
                ELSE 'Low'
            END as injury_risk_label,
            po.injury_risk as injury_risk_prob,
            po.predicted_at
        FROM predictions_output po
        LEFT JOIN team_info ti ON po.team_id = ti.team_id
        ORDER BY po.injury_risk DESC, po.performance_score DESC
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=300)
def get_team_stats_overview() -> pd.DataFrame:
    """Coach view — team-level stats."""
    query = """
        SELECT
            ti.team_long_name,
            COUNT(DISTINCT po.player_id) AS total_players,
            ROUND(AVG(po.performance_score), 1) AS avg_performance,
            ROUND(AVG(po.injury_risk) * 100, 1) AS avg_injury_risk_pct,
            SUM(CASE WHEN po.injury_risk > 0.7 THEN 1 ELSE 0 END) AS high_risk_count
        FROM predictions_output po
        LEFT JOIN team_info ti ON po.team_id = ti.team_id
        GROUP BY ti.team_long_name
        ORDER BY avg_injury_risk_pct DESC
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=300)
def get_risk_distribution() -> pd.DataFrame:
    """Injury risk distribution across all players — for coach charts."""
    query = """
        SELECT
            CASE 
                WHEN injury_risk > 0.7 THEN 'High'
                WHEN injury_risk > 0.5 THEN 'Medium'
                ELSE 'Low'
            END as injury_risk_label,
            COUNT(*) AS player_count
        FROM predictions_output
        GROUP BY 
            CASE 
                WHEN injury_risk > 0.7 THEN 'High'
                WHEN injury_risk > 0.5 THEN 'Medium'
                ELSE 'Low'
            END
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=300)
def get_performance_distribution() -> pd.DataFrame:
    """Performance score distribution — for coach histogram."""
    query = """
        SELECT player_name, performance_score
        FROM predictions_output
    """
    return pd.read_sql(query, get_engine())


def run_custom_query(sql: str) -> pd.DataFrame:
    """Runs a raw SQL query — used by the coach chatbot."""
    try:
        return pd.read_sql(sql, get_engine())
    except Exception as e:
        raise ValueError(f"Query failed: {e}")


@st.cache_data(ttl=300)
def get_all_teams() -> pd.DataFrame:
    """Get all available teams with their IDs and stats."""
    query = """
        SELECT
            ti.team_id,
            ti.team_long_name,
            COUNT(DISTINCT ps.player_id) AS total_players
        FROM team_info ti
        LEFT JOIN player_stats ps ON ti.team_id = ps.team_id
        GROUP BY ti.team_id, ti.team_long_name
        ORDER BY ti.team_long_name
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=300)
def get_team_players(team_id: int) -> pd.DataFrame:
    """Get all players for a specific team with their predictions."""
    query = f"""
        SELECT
            po.player_id,
            po.player_name,
            po.performance_score,
            CASE 
                WHEN po.injury_risk > 0.7 THEN 'High'
                WHEN po.injury_risk > 0.5 THEN 'Medium'
                ELSE 'Low'
            END as injury_risk_label,
            ROUND(po.injury_risk * 100, 1) as injury_risk_pct,
            ps.age,
            ps.potential
        FROM predictions_output po
        LEFT JOIN player_stats ps ON po.player_id = ps.player_id
        WHERE po.team_id = {team_id}
        ORDER BY po.injury_risk DESC, po.performance_score DESC
    """
    return pd.read_sql(query, get_engine())


@st.cache_data(ttl=300)
def get_team_summary(team_id: int) -> pd.DataFrame:
    """Get comprehensive stats summary for a team."""
    query = f"""
        SELECT
            ti.team_id,
            ti.team_long_name,
            COUNT(DISTINCT po.player_id) AS total_players,
            ROUND(AVG(po.performance_score), 1) AS avg_performance,
            MIN(po.performance_score) AS min_performance,
            MAX(po.performance_score) AS max_performance,
            ROUND(AVG(po.injury_risk) * 100, 1) AS avg_injury_risk_pct,
            SUM(CASE WHEN po.injury_risk > 0.7 THEN 1 ELSE 0 END) AS high_risk_players,
            SUM(CASE WHEN po.injury_risk > 0.5 AND po.injury_risk <= 0.7 THEN 1 ELSE 0 END) AS medium_risk_players,
            SUM(CASE WHEN po.injury_risk <= 0.5 THEN 1 ELSE 0 END) AS low_risk_players,
            SUM(CASE WHEN po.performance_score > 80 THEN 1 ELSE 0 END) AS high_performers,
            SUM(CASE WHEN po.performance_score >= 50 AND po.performance_score <= 80 THEN 1 ELSE 0 END) AS mid_performers,
            SUM(CASE WHEN po.performance_score < 50 THEN 1 ELSE 0 END) AS low_performers
        FROM predictions_output po
        LEFT JOIN team_info ti ON po.team_id = ti.team_id
        WHERE po.team_id = {team_id}
        GROUP BY 
            ti.team_id, 
            ti.team_long_name
    """
    return pd.read_sql(query, get_engine())