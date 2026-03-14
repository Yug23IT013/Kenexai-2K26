# ML Models Documentation

## Overview
This directory contains all trained machine learning models used in the Football Analytics Pipeline. Both models are trained on Snowflake dataset extracts and validated through comprehensive testing.

---

## 1. Injury Risk Prediction Model

**Model Type:** `LogisticRegression` (Binary Classification)  
**File:** `models/injury_model.pkl`  
**Scaler:** `models/injury_scaler.pkl`  
**Training Notebook:** `injury_risk_logistic_regression.ipynb`  
**Training Dataset:** `cleaned_player_data_logistic_reg_outliers_removed.csv`

### Target Variable
- `injury_risk` → 0 (Safe) or 1 (At Risk of Injury)

### Input Features (EXACTLY 8)
1. `matches_last_7_days` - Recent match frequency
2. `previous_injury_count` - History of injuries 
3. `fatigue_index` - Current fatigue level (0-100)
4. `training_load` - Training intensity
5. `recovery_time` - Time available for recovery (hours)
6. `minutes_played` - Total playing time
7. `potential` - Player potential rating
8. `ball_control` - Ball control skill rating

### Output
- `injury_risk_prob` → Float 0.0 to 1.0 (probability of injury)
- `injury_risk_label` → "Low" (≤0.40), "Medium" (0.40-0.70), or "High" (≥0.70)

### Fallback Scoring (When Model Fails)
Uses min-max normalized fatigue_index as proxy:
```
risk_prob = (fatigue_index - min) / (max - min)
```

---

## 2. Performance Scoring Model

**Model Type:** `LinearRegression` (Continuous Prediction)  
**File:** `models/performance_model.pkl`  
**Scaler:** `models/performance_scaler.pkl`  
**Training Notebook:** `Final Performance Model/Performance_Model_Baseline.ipynb`  
**Training Dataset:** `cleaned_player_data_performance_model_reordered.csv`  
**Ablation Study:** `Final Performance Model/Ablation_Attack_Defense.ipynb` (10 vs 8 features)

### Target Variable
- `overall_rating` → Continuous scale (player performance 0-100)

### Input Features (EXACTLY 10)
1. `potential` - Player's maximum potential
2. `reactions` - Reaction speed
3. `ball_control` - Ball handling skill
4. `dribbling` - Dribbling ability
5. `stamina` - Endurance and stamina
6. `strength` - Physical strength
7. `acceleration` - Acceleration capability
8. `balance` - Balance and coordination
9. `defensive_work_rate_encoded` - Defensive effort level
10. `attacking_work_rate_encoded` - Attacking effort level

### Output
- `performance_score` → Float 0.0 to 100.0

### Fallback Scoring (When Model Fails)
Weighted average of available attributes:
```
score = (potential × 0.3 + ball_control × 0.15 + dribbling × 0.15 + 
         acceleration × 0.15 + stamina × 0.15 + strength × 0.10)
```

---

## Snowflake Data Sources

### Source Tables
- `PLAYER_INJURY` - Injury history and risk factors (8,714 rows)
- `PLAYER_STATS` - Performance statistics (8,327 rows)
- `TEAM_INFO` - Team metadata (225 rows)
- `TEAM_STATS` - Team performance data (215 rows)

### Output Table
- `PREDICTIONS_OUTPUT` - Final model predictions
  - Columns: `player_id`, `player_name`, `team_id`, `performance_score`, `injury_risk`, `recommendation`, `predicted_at`
  - Current Records: ~8,714
  - Update Frequency: Daily (scheduled via Windows Task Scheduler)

---

## Pipeline Execution

### Standalone Execution
```bash
python run_pipeline.py
```

**Flow:**
1. Fetch player injury features from Snowflake (8,714 records)
2. Run LogisticRegression injury model on 8 features
   - Fallback: Min-max normalized fatigue_index
3. Fetch player stats features from Snowflake (8,327 records)
4. Run LinearRegression performance model on 10 features
   - Fallback: Weighted average scoring
5. Merge results by player_id
6. Generate AI-powered coaching recommendations
7. Write to `PREDICTIONS_OUTPUT` table in Snowflake
8. Display summary statistics

### Scheduled Execution
**Schedule:** Windows Task Scheduler
**Frequency:** Daily (default 6:00 AM UTC recommended)
**Script:** `schedule_pipeline.ps1`

### Airflow Orchestration (Optional)
**DAG:** `dags/athlete_performance_pipeline.py`
**Tasks:** 7-step pipeline with parallel execution
**Status:** Available but run_pipeline.py is simpler alternative

---

## Model Performance

### Injury Model (LogisticRegression)
- **Features:** 8 key risk factors
- **Training:** Sklearn LogisticRegression with Standard Scaling
- **Target:** Binary classification (injury vs safe)
- **Validation Method:** Cross-validation with Stratified K-Fold

### Performance Model (LinearRegression)
- **Features:** 10 key skill attributes
- **Training:** Sklearn LinearRegression with Standard Scaling
- **Target:** Continuous performance rating
- **Ablation Study:** 10 features (with attack/defense) vs 8 features
  - Result: 10-feature model selected (R² = 0.838759)
  - Better generalization and test performance

---

## Feature Sources

### Data Integration
All features are derived from Snowflake by joining:
- `PLAYER_INJURY` table (injury-specific metrics)
- `PLAYER_STATS` table (skill attributes)
- `TEAM_INFO` table (team context)

### Feature Engineering
- **Encoded Features:**
  - `attacking_work_rate_encoded` / `defensive_work_rate_encoded` - One-hot encoded work rate categories
  - `previous_injury_count` - Count aggregation from injury history
  
- **Calculated Features:**
  - `fatigue_index` - Derived from training load and recovery data
  - `training_load` - Aggregated from recent training sessions
  - `recovery_time` - Hours since last match/training
  - `matches_last_7_days` - Count of matches in 7-day window
  - `minutes_played` - Cumulative playing time

---

## Quality Assurance

### Model Validation Checks
✓ Correct feature count: Injury (8), Performance (10)  
✓ Feature names match Snowflake column names exactly  
✓ Fallback scoring working for both models  
✓ Predictions normalized to correct output ranges  
✓ Min-max scaling prevents display issues (e.g., 98.9 injury prob)

### Pipeline Testing
✓ Data fetching: 8,714 injury records, 8,327 performance records  
✓ Model inference: Both models execute or fallback gracefully  
✓ Snowflake write: 8,714+ predictions successfully stored  
✓ Streamlit display: Live data from PREDICTIONS_OUTPUT  
✓ Recommendations: AI-generated for all players  

---

## Troubleshooting

### Issue: "X has 17 features, but LogisticRegression is expecting 8"
**Cause:** injury_predictor.py listing wrong features  
**Solution:** Update INJURY_FEATURES list with correct 8 features (DONE)

### Issue: "Injury risk shows 98.9 for all players"
**Cause:** Fallback using `fatigue_index / 100` directly  
**Solution:** Use min-max normalization instead (DONE)

### Issue: "Performance model error: X has 16 features, but LinearRegression is expecting 10"
**Cause:** performance_scorer.py listing wrong features  
**Solution:** Update PERFORMANCE_FEATURES list with correct 10 features (DONE)

### Issue: Model file not found
**Solution:**
```bash
python inspect_models.py  # Verify models exist
python save_models.py      # Save from training notebooks if needed
```

---

## Model Coefficients

### Injury Model (LogisticRegression)
Trained coefficients stored in `injury_model.pkl`  
Access via: `model.coef_` and `model.intercept_`

### Performance Model (LinearRegression)
Trained coefficients stored in `performance_model.pkl`  
Access via: `model.coef_` and `model.intercept_`

---

## Metadata Reference

**File:** `models/metadata/models_metadata.json`

Contains:
- Model names and types
- Training notebooks
- Target and feature definitions
- Model file paths
- Training datasets

---

**Last Updated:** March 15, 2026  
**Status:** ✓ Production Ready  
**Next Review:** March 22, 2026
