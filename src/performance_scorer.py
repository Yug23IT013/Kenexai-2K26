import os
import joblib
import pandas as pd
import numpy as np

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "performance_model.pkl")

# Features your performance model was trained on — EXACTLY 10 features
# ✓ Verified from: models/metadata/models_metadata.json & Final Performance Model/Ablation_Attack_Defense.ipynb
PERFORMANCE_FEATURES = [
    "potential",
    "reactions",
    "ball_control",
    "dribbling",
    "stamina",
    "strength",
    "acceleration",
    "balance",
    "defensive_work_rate_encoded",
    "attacking_work_rate_encoded",
]

# Weights for rule-based fallback scoring (0–100 scale)
# Used if no performance_model.pkl exists
SCORE_WEIGHTS = {
    "ball_control":   0.15,
    "dribbling":      0.12,
    "stamina":        0.12,
    "reactions":      0.12,
    "acceleration":   0.10,
    "strength":       0.08,
    "balance":        0.08,
    "potential":      0.13,
    "buildupplayspeed":        0.05,
    "chancecreationshooting":  0.05,
}


def _rule_based_score(df: pd.DataFrame) -> np.ndarray:
    """
    Fallback weighted average score if no trained model is available.
    Returns scores normalized to 0–100.
    """
    score = pd.Series(np.zeros(len(df)), index=df.index)
    for col, weight in SCORE_WEIGHTS.items():
        if col in df.columns:
            # Normalize each column to 0–1 before applying weight
            col_min = df[col].min()
            col_max = df[col].max()
            if col_max > col_min:
                normalized = (df[col] - col_min) / (col_max - col_min)
            else:
                normalized = pd.Series(np.zeros(len(df)), index=df.index)
            score += normalized * weight * 100

    return np.round(score.values, 2)


def compute_performance_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a dataframe from fetch_player_stats_features()
    and returns it with performance_score column added (0–100).

    Args:
        df: DataFrame from db_utils.fetch_player_stats_features()

    Returns:
        DataFrame with player_id, player_name, team_long_name,
        performance_score
    """
    X = df.copy()
    X = X.fillna(X.select_dtypes(include=[np.number]).median())

    # Try ML model first, fall back to rule-based scoring
    if os.path.exists(MODEL_PATH):
        print("  Using trained performance model (pkl).")
        try:
            model = joblib.load(MODEL_PATH)
            
            # Load scaler if available
            SCALER_PATH = os.path.join(BASE_DIR, "models", "performance_scaler.pkl")
            scaler = joblib.load(SCALER_PATH) if os.path.exists(SCALER_PATH) else None

            missing = [f for f in PERFORMANCE_FEATURES if f not in X.columns]
            if missing:
                print(f"  [WARN] Missing features for model: {missing}. Using rule-based fallback.")
                scores = _rule_based_score(X)
            else:
                # Scale features using scaler
                X_selected = X[PERFORMANCE_FEATURES].copy()
                if scaler is not None:
                    X_scaled = scaler.transform(X_selected)
                else:
                    X_scaled = X_selected
                
                # Get raw predictions
                raw_scores = model.predict(X_scaled)
                
                # The model outputs are in a large scale, normalize to 0-100
                # Assuming overall_rating should be normalized to 0-100
                # Use percentile-based normalization
                q1, q99 = np.percentile(raw_scores, [1, 99])
                scores = np.clip((raw_scores - q1) / (q99 - q1) * 100, 0, 100)
                scores = np.round(scores, 2)
        except Exception as e:
            print(f"  [WARN] Model prediction failed: {e}. Using rule-based fallback.")
            scores = _rule_based_score(X)
    else:
        print("  No performance model found — using rule-based scoring.")
        scores = _rule_based_score(X)

    result = df[["player_id", "player_name", "team_id", "team_long_name"]].copy()
    result["performance_score"] = scores
    
    print(f"  Performance scores computed for {len(result)} players.")
    print(f"  Score range: {scores.min():.1f} – {scores.max():.1f}")

    return result