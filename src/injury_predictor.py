import os
import joblib
import pandas as pd
import numpy as np

# Use absolute path so Airflow can find the model
# regardless of where it is invoked from
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "injury_model.pkl")

# Features your injury model was trained on — EXACTLY 8 features
# ✓ Verified from: models/metadata/models_metadata.json & training notebook
INJURY_FEATURES = [
    "matches_last_7_days",
    "previous_injury_count",
    "fatigue_index",
    "training_load",
    "recovery_time",
    "minutes_played",
    "potential",
    "ball_control",
]


def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Injury model not found at {MODEL_PATH}. "
            "Run save_models.py first."
        )
    return joblib.load(MODEL_PATH)


def predict_injury_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a dataframe from fetch_player_injury_features()
    and returns it with two new columns added:
        injury_risk_prob  — float 0.0 to 1.0
        injury_risk_label — 'Low', 'Medium', or 'High'

    Args:
        df: DataFrame from db_utils.fetch_player_injury_features()

    Returns:
        DataFrame with player_id, player_name, team_long_name,
        injury_risk_prob, injury_risk_label
    """
    model = load_model()

    # Check all required features are present
    missing = [f for f in INJURY_FEATURES if f not in df.columns]
    if missing:
        raise ValueError(
            f"Missing feature columns in input data: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )

    X = df[INJURY_FEATURES].copy()

    # Handle any nulls — fill with column median
    X = X.fillna(X.median())

    # Load scaler if available
    SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "injury_scaler.pkl")
    scaler = joblib.load(SCALER_PATH) if os.path.exists(SCALER_PATH) else None
    
    # Scale features if scaler exists
    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X

    # Predict probability of injury (class 1)
    probs = model.predict_proba(X_scaled)[:, 1]

    result = df[["player_id", "player_name", "team_id", "team_long_name"]].copy()
    result["injury_risk_prob"]  = np.round(probs, 4)
    result["injury_risk_label"] = result["injury_risk_prob"].apply(
        lambda p: "High"   if p >= 0.70 else
                  "Medium" if p >= 0.40 else
                  "Low"
    )

    print(f"  Injury predictions complete for {len(result)} players.")
    print(f"  Risk distribution:\n{result['injury_risk_label'].value_counts().to_string()}")

    return result