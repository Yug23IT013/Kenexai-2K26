import os
import pandas as pd
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL
from dotenv import load_dotenv

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


def get_engine():
    return create_engine(URL(**SNOWFLAKE_CONFIG))


# ── READ FUNCTIONS ──────────────────────────────────────────────

def fetch_player_injury_features() -> pd.DataFrame:
    """
    Fetches all feature columns needed by injury_predictor.py
    from player_injury joined with team_info.
    """
    query = """
        SELECT
            pi.player_id,
            pi.player_name,
            pi.team_id,
            ti.team_long_name,
            pi.potential,
            pi.ball_control,
            pi.dribbling,
            pi.stamina,
            pi.reactions,
            pi.balance,
            pi.strength,
            pi.acceleration,
            pi.age,
            pi.attacking_work_rate_encoded,
            pi.defensive_work_rate_encoded,
            pi.fatigue_index,
            pi.matches_last_7_days,
            pi.minutes_played,
            pi.recovery_time,
            pi.previous_injury_count,
            pi.training_load,
            pi.injury_risk
        FROM player_injury pi
        JOIN team_info ti ON pi.team_id = ti.team_id
    """
    return pd.read_sql(query, get_engine())


def fetch_player_stats_features() -> pd.DataFrame:
    """
    Fetches all feature columns needed by performance_scorer.py
    from player_stats joined with team_stats and team_info.
    """
    query = """
        SELECT
            ps.player_id,
            ps.player_name,
            ps.team_id,
            ti.team_long_name,
            ps.potential,
            ps.ball_control,
            ps.dribbling,
            ps.stamina,
            ps.reactions,
            ps.balance,
            ps.strength,
            ps.acceleration,
            ps.age,
            ps.attacking_work_rate_encoded,
            ps.defensive_work_rate_encoded,
            ts.buildupplayspeed,
            ts.buildupplaypassing,
            ts.chancecreationshooting,
            ts.defencepressure,
            ts.defenceaggression
        FROM player_stats ps
        JOIN team_info  ti ON ps.team_id = ti.team_id
        JOIN team_stats ts ON ps.team_id = ts.team_id
    """
    return pd.read_sql(query, get_engine())


def fetch_all_players() -> pd.DataFrame:
    """Lightweight fetch — used by genai_recommender for player context."""
    query = """
        SELECT
            pi.player_id,
            pi.player_name,
            ti.team_long_name,
            pi.age,
            pi.fatigue_index,
            pi.training_load,
            pi.minutes_played,
            pi.previous_injury
        FROM player_injury pi
        JOIN team_info ti ON pi.team_id = ti.team_id
    """
    return pd.read_sql(query, get_engine())


# ── WRITE FUNCTIONS ─────────────────────────────────────────────

def write_predictions(df: pd.DataFrame) -> None:
    """
    Writes the final predictions dataframe to predictions_output table.
    Expected columns:
        player_id, player_name, team_long_name,
        performance_score, injury_risk_label,
        injury_risk_prob, recommendation
    """
    df.columns = [c.lower() for c in df.columns]
    df.to_sql(
        name="predictions_output",
        con=get_engine(),
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )
    print(f"  Wrote {len(df)} prediction rows to Snowflake.")


def read_latest_predictions() -> pd.DataFrame:
    """Used by Streamlit to fetch the most recent prediction run."""
    query = """
        SELECT
            p.*,
            ti.team_long_name
        FROM predictions_output p
        JOIN team_info ti ON p.team_id = ti.team_id
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY p.player_id
            ORDER BY p.predicted_at DESC
        ) = 1
        ORDER BY p.injury_risk_prob DESC
    """
    return pd.read_sql(query, get_engine())