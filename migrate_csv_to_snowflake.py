import pandas as pd
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL
import os

# ─────────────────────────────────────────
# SNOWFLAKE CONNECTION CONFIG
# ─────────────────────────────────────────
SNOWFLAKE_CONFIG = {
    "account":   "your_snowflake_account_here",
    "user":      "MARK",
    "password":  "492005M@rk1234",
    "database":  "sports_db",
    "schema":    "analytics",
    "warehouse": "sports_wh",
    "role":      "ACCOUNTADMIN",
}

# ─────────────────────────────────────────
# CSV FILE PATHS — update these to your actual file locations
# ─────────────────────────────────────────
CSV_PATHS = {
    "team_info":     "FinalDataset2/cleaned_team_master_alpha_only.csv",
    "team_stats":    "FinalDataset2/cleaned_team_data_alpha_only.csv",
    "player_stats":  "FinalDataset2/cleaned_player_data_performance_model_reordered_consistent.csv",
    "player_injury": "FinalDataset2/cleaned_player_data_injury_risk_reordered_consistent.csv",
}

# ─────────────────────────────────────────
# EXPECTED COLUMNS PER TABLE (matches your schema exactly)
# ─────────────────────────────────────────
EXPECTED_COLUMNS = {
    "team_info": [
        "team_id", "team_long_name", "team_short_name"
    ],
    "team_stats": [
        "team_id", "team_long_name", "team_short_name",
        "buildUpPlaySpeed", "buildUpPlayDribbling", "buildUpPlayPassing",
        "chanceCreationPassing", "chanceCreationCrossing", "chanceCreationShooting",
        "defencePressure", "defenceAggression", "defenceTeamWidth"
    ],
    "player_stats": [
        "player_id", "player_name", "team_id", "potential",
        "ball_control", "dribbling", "stamina", "reactions",
        "balance", "strength", "acceleration", "age",
        "attacking_work_rate_encoded", "defensive_work_rate_encoded",
        "overall_rating"
    ],
    "player_injury": [
        "player_id", "player_name", "team_id", "potential",
        "ball_control", "dribbling", "stamina", "reactions",
        "balance", "strength", "acceleration", "age",
        "attacking_work_rate_encoded", "defensive_work_rate_encoded",
        "fatigue_index", "matches_last_7_days", "minutes_played",
        "recovery_time", "previous_injury_count", "training_load", "injury_risk"
    ],
}

# ─────────────────────────────────────────
# COLUMN DATA TYPES FOR VALIDATION
# ─────────────────────────────────────────
INT_COLUMNS = {
    "team_info":     ["team_id"],
    "team_stats":    ["team_id", "buildUpPlaySpeed", "buildUpPlayDribbling",
                      "buildUpPlayPassing", "chanceCreationPassing",
                      "chanceCreationCrossing", "chanceCreationShooting",
                      "defencePressure", "defenceAggression", "defenceTeamWidth"],
    "player_stats":  ["player_id", "team_id", "potential", "ball_control",
                      "dribbling", "stamina", "reactions", "balance",
                      "strength", "acceleration", "age",
                      "attacking_work_rate_encoded",
                      "defensive_work_rate_encoded", "overall_rating"],
    "player_injury": ["player_id", "team_id", "potential", "ball_control",
                      "dribbling", "stamina", "reactions", "balance",
                      "strength", "acceleration", "age",
                      "attacking_work_rate_encoded",
                      "defensive_work_rate_encoded",
                      "matches_last_7_days", "minutes_played",
                      "previous_injury_count", "injury_risk"],
}

FLOAT_COLUMNS = {
    "player_injury": ["fatigue_index", "recovery_time", "training_load"],
}


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def get_engine():
    print("  Connecting to Snowflake...")
    engine = create_engine(URL(**SNOWFLAKE_CONFIG))
    print("  Connected.")
    return engine


def load_csv(table_name: str, path: str) -> pd.DataFrame:
    print(f"  Loading CSV: {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def validate_columns(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Keep only the columns defined in your schema, warn on missing ones."""
    expected = EXPECTED_COLUMNS[table_name]
    missing = [c for c in expected if c not in df.columns]
    extra   = [c for c in df.columns if c not in expected]

    if missing:
        raise ValueError(
            f"  [ERROR] {table_name}: missing required columns: {missing}\n"
            f"  Your CSV has: {list(df.columns)}"
        )
    if extra:
        print(f"  [WARN]  {table_name}: dropping extra columns not in schema: {extra}")

    return df[expected]


def enforce_types(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Cast columns to correct types to avoid Snowflake type errors."""
    for col in INT_COLUMNS.get(table_name, []):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in FLOAT_COLUMNS.get(table_name, []):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)

    return df


def clean_dataframe(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Lowercase column names — Snowflake stores unquoted names in uppercase,
    snowflake-sqlalchemy handles the mapping when columns are lowercase."""
    df.columns = [c.lower() for c in df.columns]

    # Drop fully duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    if removed:
        print(f"  [INFO]  Removed {removed} duplicate rows from {table_name}")

    return df


def upload_table(df: pd.DataFrame, table_name: str, engine) -> None:
    print(f"  Uploading {len(df)} rows to '{table_name}'...")
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="replace",          # Replace tables to ensure schema matches CSV
        index=False,
        method="multi",           # multi-row insert — much faster on Snowflake
        chunksize=100,            # Reduced from 500 to avoid Snowflake statement size limits
    )
    print(f"  Done uploading '{table_name}'.")


def verify_upload(table_name: str, engine) -> None:
    result = pd.read_sql(f"SELECT COUNT(*) AS cnt FROM {table_name}", engine)
    count  = result["cnt"].iloc[0]
    print(f"  Verified: '{table_name}' now has {count} rows in Snowflake.")


# ─────────────────────────────────────────
# MIGRATION ORDER
# team_info first — it is the parent table (other tables FK to it)
# team_stats second — FKs to team_info
# player_stats third — FKs to team_info
# player_injury last — FKs to team_info
# ─────────────────────────────────────────
MIGRATION_ORDER = ["team_info", "team_stats", "player_stats", "player_injury"]


def migrate():
    print("\n=== Athlete Analytics — CSV to Snowflake Migration ===\n")
    engine = get_engine()

    for table_name in MIGRATION_ORDER:
        print(f"\n[{table_name}]")
        try:
            # 1. Load
            df = load_csv(table_name, CSV_PATHS[table_name])

            # 2. Validate columns
            df = validate_columns(df, table_name)

            # 3. Enforce types
            df = enforce_types(df, table_name)

            # 4. Clean
            df = clean_dataframe(df, table_name)

            # 5. Upload
            upload_table(df, table_name, engine)

            # 6. Verify
            verify_upload(table_name, engine)

        except FileNotFoundError as e:
            print(f"  [SKIP] {e}")
        except ValueError as e:
            print(f"  [FAIL] {e}")
            raise
        except Exception as e:
            print(f"  [FAIL] Unexpected error on '{table_name}': {e}")
            raise

    print("\n=== Migration complete ===\n")


# ─────────────────────────────────────────
# OPTIONAL: preview what's in Snowflake after migration
# ─────────────────────────────────────────
def preview_tables():
    engine = get_engine()
    for table in MIGRATION_ORDER:
        print(f"\n--- {table} (first 3 rows) ---")
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 3", engine)
        print(df.to_string(index=False))


if __name__ == "__main__":
    migrate()
    preview_tables()