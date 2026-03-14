import pandas as pd
import numpy as np

# ── Reproducibility ──────────────────────────────────────────────────────
np.random.seed(42)

# ── Load ─────────────────────────────────────────────────────────────────
INPUT  = "cleaned_player_data_performance_model_outliers_removed.csv"
OUTPUT = "cleaned_player_data_performance_model_outliers_removed.csv"

df = pd.read_csv(INPUT)
n = len(df)

# ── Helper ───────────────────────────────────────────────────────────────
def clamp(arr, lo, hi):
    return np.clip(arr, lo, hi)

def norm(series):
    """Min-max normalise to 0-1."""
    mn, mx = series.min(), series.max()
    return (series - mn) / max(mx - mn, 1e-9)

# =========================================================================
# Available player features:
#   overall_rating, potential, ball_control, dribbling, stamina,
#   reactions, balance, strength, acceleration, age,
#   attacking_work_rate, defensive_work_rate
# =========================================================================

# Encode work rates numerically for formulas
awr_map = {"low": 1, "medium": 2, "high": 3}
dwr_map = {"low": 1, "medium": 2, "high": 3}
awr = df["attacking_work_rate"].str.strip().str.lower().map(awr_map).fillna(2)
dwr = df["defensive_work_rate"].str.strip().str.lower().map(dwr_map).fillna(2)

# ────────────────────────────────────────────────────────────────────────
# 1) fatigue_index (0–100)
#    Real-world logic: Players with LOW stamina, HIGH work rate, and
#    OLDER age fatigue faster.  Acceleration demands also drain energy.
#    Formula: inverse stamina + work-rate intensity + age factor
# ────────────────────────────────────────────────────────────────────────
inv_stamina = 100 - df["stamina"]            # lower stamina → higher fatigue base
work_intensity = (awr + dwr) / 6 * 100       # 0-100 scale from work rates
age_factor = norm(df["age"]) * 40            # older → +0..40

fatigue_raw = (
    0.40 * inv_stamina
    + 0.25 * work_intensity
    + 0.20 * age_factor
    + 0.15 * (100 - df["acceleration"])       # low acceleration = heavy legs
)
df["fatigue_index"] = clamp(
    norm(fatigue_raw) * 100 + np.random.normal(0, 6, n), 0, 100
).round(1)

# ────────────────────────────────────────────────────────────────────────
# 2) matches_last_7_days (1–3)
#    Real-world logic: Higher-rated players are starters → play more
#    fixtures.  High work-rate players also deployed more often.
# ────────────────────────────────────────────────────────────────────────
play_demand = norm(df["overall_rating"]) * 0.6 + norm(awr + dwr) * 0.4
# probability weights for 1 / 2 / 3 matches
p1 = 0.45 - 0.20 * play_demand
p3 = 0.10 + 0.20 * play_demand
p2 = 1 - p1 - p3
probs = np.column_stack([p1, p2, p3])
probs = probs / probs.sum(axis=1, keepdims=True)
df["matches_last_7_days"] = [
    np.random.choice([1, 2, 3], p=probs[i]) for i in range(n)
]

# ────────────────────────────────────────────────────────────────────────
# 3) minutes_played (900–4500, season total)
#    Real-world logic: Better-rated & higher-potential players get more
#    game time.  Young high-potential players are also given minutes.
#    Stamina allows them to last longer per match.
# ────────────────────────────────────────────────────────────────────────
mins_base = (
    0.40 * norm(df["overall_rating"])
    + 0.25 * norm(df["potential"])
    + 0.20 * norm(df["stamina"])
    + 0.15 * norm(df["reactions"])
)
df["minutes_played"] = clamp(
    900 + mins_base * 3200 + np.random.normal(0, 300, n),
    900, 4500
).astype(int)

# ────────────────────────────────────────────────────────────────────────
# 4) recovery_time (12–72 hours)
#    Real-world logic: Recovery depends on age (older = slower), stamina
#    (higher stamina = faster recovery), and strength (stronger muscles
#    recover quicker).  Inverse relationship.
# ────────────────────────────────────────────────────────────────────────
recovery_ability = (
    0.40 * norm(df["stamina"])
    + 0.30 * norm(df["strength"])
    + 0.30 * (1 - norm(df["age"]))  # younger recovers faster
)
# high recovery_ability → low hours, low ability → high hours
df["recovery_time"] = clamp(
    72 - recovery_ability * 55 + np.random.normal(0, 4, n),
    12, 72
).round(1)

# ────────────────────────────────────────────────────────────────────────
# 5) previous_injury_count (0–5)
#    Real-world logic: Older players accumulate more injuries over career.
#    Low balance + high acceleration = muscle-pull prone (explosive but
#    unstable).  High strength is protective.
# ────────────────────────────────────────────────────────────────────────
injury_propensity = (
    0.35 * norm(df["age"])                    # older → more history
    + 0.25 * (1 - norm(df["balance"]))        # poor balance → injury prone
    + 0.20 * norm(df["acceleration"])          # explosive players pull muscles
    + 0.20 * (1 - norm(df["strength"]))        # weak → injury susceptible
)
lam = injury_propensity * 3.5   # Poisson lambda
raw_injuries = np.array([np.random.poisson(l) for l in lam])
df["previous_injury_count"] = clamp(raw_injuries, 0, 5).astype(int)

# ────────────────────────────────────────────────────────────────────────
# 6) training_load (1–10)
#    Real-world logic: Players with high potential (developing) and high
#    work-rate train harder.  Dribbling & ball-control improvement
#    requires intensive technical sessions.
# ────────────────────────────────────────────────────────────────────────
train_raw = (
    0.30 * norm(df["potential"])
    + 0.25 * norm(awr + dwr)
    + 0.25 * norm(df["dribbling"])
    + 0.20 * norm(df["ball_control"])
)
df["training_load"] = clamp(
    1 + train_raw * 9 + np.random.normal(0, 0.7, n),
    1, 10
).round(1)

# ────────────────────────────────────────────────────────────────────────
# 7) injury_risk (0 / 1)  — BINARY TARGET
#    Composite score from all 6 features + underlying player attributes.
#    Threshold at ~70th percentile → ~30% positive (realistic rate).
# ────────────────────────────────────────────────────────────────────────
risk_score = (
    0.22 * norm(df["fatigue_index"])
    + 0.18 * (df["matches_last_7_days"] / 3)
    + 0.14 * norm(df["minutes_played"])
    + 0.16 * norm(df["recovery_time"])          # high recovery_time = slow = risky
    + 0.16 * (df["previous_injury_count"] / 5)
    + 0.14 * norm(df["training_load"])
)
# Add noise so model boundary is not trivially separable
risk_score += np.random.normal(0, 0.05, n)
threshold = np.percentile(risk_score, 70)
df["injury_risk"] = (risk_score >= threshold).astype(int)

# ── Save ─────────────────────────────────────────────────────────────────
df.to_csv(OUTPUT, index=False)

# ── Summary ──────────────────────────────────────────────────────────────
new_cols = [
    "fatigue_index", "matches_last_7_days", "minutes_played",
    "recovery_time", "previous_injury_count", "training_load", "injury_risk",
]
print("=" * 65)
print(f"  Rows: {len(df)}  |  Total Columns: {len(df.columns)}")
print("=" * 65)
print("\n--- New Columns Summary ---")
print(df[new_cols].describe().round(2).to_string())
print(f"\n--- injury_risk class distribution ---")
print(df["injury_risk"].value_counts().sort_index().to_string())
print(f"\n--- Null check (new columns) ---")
print(df[new_cols].isnull().sum().to_string())
print(f"\n--- Correlation with injury_risk ---")
for c in new_cols[:-1]:
    print(f"  {c:>25s}  →  {df[c].corr(df['injury_risk']):.3f}")
print(f"\nSaved → {OUTPUT}")
