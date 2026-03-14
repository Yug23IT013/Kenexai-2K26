# ML Models Organization Structure

## Current Setup

```
Football/
├── ml_models/                          [NEW - Model Documentation]
│   └── README_MODELS.md               [Complete model documentation]
│
├── models/                            [Trained Models]
│   ├── injury_model.pkl               [LogisticRegression - 8 features]
│   ├── injury_scaler.pkl              [StandardScaler for injury model]
│   ├── performance_model.pkl          [LinearRegression - 10 features]
│   ├── performance_scaler.pkl         [StandardScaler for performance model]
│   └── metadata/
│       └── models_metadata.json       [Feature lists and model info]
│
├── src/                               [Pipeline Code]
│   ├── injury_predictor.py            [✓ FIXED: 8 correct features]
│   ├── performance_scorer.py          [✓ FIXED: 10 correct features]
│   ├── genai_recommender.py           [Coaching recommendations]
│   ├── db_utils.py                    [Snowflake queries]
│   └── athlete_pipeline.py            [Airflow DAG tasks]
│
├── run_pipeline.py                    [✓ FIXED: Fallback scoring normalization]
├── streamlit_app/                     [Streamlit Frontend]
├── Final Dataset/                     [Training data (archive)]
├── FinalDataset2/                     [Training data (archive)]
└── Final Performance Model/           [Training notebooks (archive)]
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SNOWFLAKE DATABASE (Raw Data)                                   │
│ - PLAYER_INJURY table (8,714 rows)                             │
│ - PLAYER_STATS table (8,327 rows)                              │
│ - TEAM_INFO table (225 rows)                                    │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ run_pipeline.py                                                  │
│ ─ STEP 1: Fetch Features from Snowflake                        │
└───────────┬──────────────────────────┬──────────────────────────┘
            │                          │
            ▼                          ▼
    ┌───────────────────┐     ┌────────────────────┐
    │ fetch_player_     │     │ fetch_player_      │
    │ injury_features() │     │ stats_features()   │
    │                   │     │                    │
    │ 17 columns from   │     │ 16 columns from    │
    │ PLAYER_INJURY +   │     │ PLAYER_STATS +     │
    │ TEAM_INFO join    │     │ TEAM_INFO join     │
    │                   │     │                    │
    │ Returns:          │     │ Returns:           │
    │ 8,714 records     │     │ 8,327 records      │
    └────────┬──────────┘     └────────┬───────────┘
             │                         │
             ▼                         ▼
    ┌──────────────────────┐   ┌──────────────────────┐
    │ Select 8 Features:   │   │ Select 10 Features:  │
    │ 1. matches_last_7_d  │   │ 1. potential         │
    │ 2. prev_inj_count    │   │ 2. reactions         │
    │ 3. fatigue_index     │   │ 3. ball_control      │
    │ 4. training_load     │   │ 4. dribbling         │
    │ 5. recovery_time     │   │ 5. stamina           │
    │ 6. minutes_played    │   │ 6. strength          │
    │ 7. potential         │   │ 7. acceleration      │
    │ 8. ball_control      │   │ 8. balance           │
    │                      │   │ 9. defense_work_rate │
    │                      │   │ 10. attack_work_rate │
    └────────┬─────────────┘   └────────┬─────────────┘
             │                          │
             ▼                          ▼
    ┌──────────────────────────┐  ┌─────────────────────┐
    │ INJURY MODEL             │  │ PERFORMANCE MODEL  │
    │ LogisticRegression       │  │ LinearRegression   │
    │ (8 features)             │  │ (10 features)      │
    │                          │  │                    │
    │ Output:                  │  │ Output:            │
    │ injury_risk_prob (0-1)   │  │ perf_score (0-100) │
    │ injury_risk_label        │  │                    │
    │                          │  │                    │
    │ FALLBACK (if fails):     │  │ FALLBACK (if fails)│
    │ Min-max normalized       │  │ Weighted avg:      │
    │ fatigue_index            │  │ - potential (0.3)  │
    │                          │  │ - ball_ctrl (0.15) │
    │                          │  │ - dribbling (0.15) │
    │                          │  │ - accel (0.15)     │
    │                          │  │ - stamina (0.15)   │
    │                          │  │ - strength (0.10)  │
    └────────┬─────────────────┘  └────────┬──────────┘
             │                            │
             └──────────────┬─────────────┘
                            │
                            ▼
                 ┌──────────────────────────┐
                 │ STEP 4: Merge Results    │
                 │ Join on player_id        │
                 │ 8,714 records            │
                 └──────────┬───────────────┘
                            │
                            ▼
                 ┌──────────────────────────┐
                 │ STEP 5: Generate          │
                 │ Recommendations (Groq AI) │
                 └──────────┬───────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ SNOWFLAKE: PREDICTIONS_OUTPUT Table                             │
│                                                                  │
│ Columns:                                                        │
│ - player_id, player_name, team_id                              │
│ - performance_score (0-100)                                    │
│ - injury_risk (0-100) [converted from 0-1 prob]              │
│ - recommendation (text)                                        │
│ - predicted_at (timestamp)                                    │
│                                                                  │
│ Records: 8,714 new predictions written                         │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ STREAMLIT DASHBOARD (Port 8501)                                 │
│ Displays real ML predictions                                    │
│ - Coach dashboard: Team overview, player search                │
│ - Player dashboard: Personal performance & injury risk         │
└──────────────────────────────────────────────────────────────────┘
```

## Key Improvements Made

### Fixed Issues ✓

1. **Feature Mismatch**
   - Injury: Was listing 17 features → Now correctly 8 features
   - Performance: Was listing 16 features → Now correctly 10 features
   - Source: Verified from metadata.json and training notebooks

2. **Injury Risk Display Bug**
   - Was: `injury_risk_prob = fatigue_index / 100` (e.g., 98.9/100 = 0.989)
   - Now: `injury_risk_prob = min-max_normalized(fatigue_index)`
   - Result: Proper distribution across 0.0-1.0 range

3. **Model Organization**
   - Created `ml_models/` folder with comprehensive documentation
   - Documented all feature lists and sources
   - Created fallback scoring logic for both models

### Documentation ✓
- `ml_models/README_MODELS.md` - Complete model documentation
- Feature lists with sources
- Pipeline flow documentation
- Troubleshooting guide

---

## Archive Candidates (Can be moved to archive/)

**CSV/Data Files** (already in Snowflake):
- `cleaned_player_data_logistic_reg_outliers_removed.csv`
- `Final Dataset/cleaned_player_data_performance_model_reordered.csv`
- `FinalDataset2/*.csv` files
- `main_tables/*.csv` files

**Notebooks** (training only, models already saved):
- `injury_risk_eda.ipynb`
- `injury_risk_logistic_regression.ipynb`
- `Final Performance Model/*.ipynb`

**Setup Files** (one-time only):
- `SETUP_CHECKLIST.md`
- `CONSOLIDATION_*.md`
- `DEPLOYMENT_COMPLETE.md`
- `setup_*.bat`, `setup_*.ps1`
- `AIRFLOW_SETUP.py`
- `DAG_QUICKSTART.py`

**Utility Scripts** (legacy):
- `populate_predictions.py` (replaced by run_pipeline.py)
- `save_models.py` (models already saved)
- `migrate_csv_to_snowflake.py` (data already migrated)
- `test_snowflake.py`
- Various `check_*.py` scripts

---

## Next: Run Updated Pipeline

The pipeline now has:
✓ Correct feature lists (8 and 10 features)
✓ Fixed fallback injury scoring (min-max normalized)
✓ Proper Snowflake integration
✓ AI recommendations

Ready to test with:
```bash
python run_pipeline.py
```

Expected results:
- Clean injury risk distribution (not all 98.9)
- Proper performance scores (0-100)
- AI-generated recommendations
- 8,714 predictions in PREDICTIONS_OUTPUT
