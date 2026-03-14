"""
Save Trained Models to Disk
=============================
This script saves the trained models from both notebooks to disk for later use.

IMPORTANT: Run this script AFTER both notebooks have been executed with models trained.
The models must be in memory in their respective notebooks.

Models being saved:
  1. injury_model: LogisticRegression from injury_risk_logistic_regression.ipynb
  2. performance_model: LinearRegression from Final Performance Model/Performance_Model_Baseline.ipynb

Usage:
  1. Execute injury_risk_logistic_regression.ipynb fully
  2. Execute Final Performance Model/Performance_Model_Baseline.ipynb fully
  3. Run this script: python save_models.py
"""

import joblib
import os
import pickle
from pathlib import Path


# Create models directory
os.makedirs("models", exist_ok=True)
os.makedirs("models/metadata", exist_ok=True)

print("\n" + "="*70)
print("SAVING TRAINED MODELS")
print("="*70 + "\n")

# ─────────────────────────────────────────────────────────────────────
# SAVE INJURY RISK MODEL (from injury_risk_logistic_regression.ipynb)
# ─────────────────────────────────────────────────────────────────────

print("[1] Injury Risk Model (LogisticRegression)")
print("-" * 70)

try:
    # Import the notebook to get the trained model
    # Note: This requires nbimport or manually saving from notebook
    
    # Method 1: If you've exported the model variable from the notebook
    # In your notebook, add before running this script:
    #   import joblib
    #   joblib.dump(model, '../models/injury_model.pkl')
    #   joblib.dump(scaler, '../models/injury_scaler.pkl')
    
    # For now, we'll document the expected location
    injury_model_path = "models/injury_model.pkl"
    injury_scaler_path = "models/injury_scaler.pkl"
    
    if os.path.exists(injury_model_path):
        print(f"  ✓ Found: {injury_model_path}")
        model_size = os.path.getsize(injury_model_path) / 1024
        print(f"  ✓ File size: {model_size:.2f} KB")
    else:
        print(f"  ⚠ NOT FOUND: {injury_model_path}")
        print("  → To save the injury model, run this in the notebook:")
        print("      import joblib")
        print("      joblib.dump(model, '../models/injury_model.pkl')")
        print("      joblib.dump(scaler, '../models/injury_scaler.pkl')")
        
except Exception as e:
    print(f"  ✗ Error with injury model: {e}")

print()

# ─────────────────────────────────────────────────────────────────────
# SAVE PERFORMANCE MODEL (from Performance_Model_Baseline.ipynb)
# ─────────────────────────────────────────────────────────────────────

print("[2] Performance Model (LinearRegression)")
print("-" * 70)

try:
    performance_model_path = "models/performance_model.pkl"
    performance_scaler_path = "models/performance_scaler.pkl"
    
    if os.path.exists(performance_model_path):
        print(f"  ✓ Found: {performance_model_path}")
        model_size = os.path.getsize(performance_model_path) / 1024
        print(f"  ✓ File size: {model_size:.2f} KB")
    else:
        print(f"  ⚠ NOT FOUND: {performance_model_path}")
        print("  → To save the performance model, run this in the notebook:")
        print("      import joblib")
        print("      joblib.dump(model, 'models/performance_model.pkl')")
        print("      joblib.dump(scaler, 'models/performance_scaler.pkl')")
        
except Exception as e:
    print(f"  ✗ Error with performance model: {e}")

print()

# ─────────────────────────────────────────────────────────────────────
# SAVE MODEL METADATA
# ─────────────────────────────────────────────────────────────────────

print("[3] Model Metadata")
print("-" * 70)

metadata = {
    "injury_risk_model": {
        "name": "LogisticRegression",
        "notebook": "injury_risk_logistic_regression.ipynb",
        "task": "Binary classification - Injury Risk Prediction",
        "target": "injury_risk (0=Safe, 1=Injured)",
        "features": [
            "matches_last_7_days",
            "previous_injury_count",
            "fatigue_index",
            "training_load",
            "recovery_time",
            "minutes_played",
            "potential",
            "ball_control"
        ],
        "model_file": "models/injury_model.pkl",
        "scaler_file": "models/injury_scaler.pkl"
    },
    "performance_model": {
        "name": "LinearRegression",
        "notebook": "Final Performance Model/Performance_Model_Baseline.ipynb",
        "task": "Regression - Player Performance Prediction",
        "target": "overall_rating (continuous scale)",
        "features": "See notebook for complete feature list",
        "model_file": "models/performance_model.pkl",
        "scaler_file": "models/performance_scaler.pkl"
    }
}

# Save metadata as JSON
import json
metadata_path = "models/metadata/models_metadata.json"
with open(metadata_path, "w") as f:
    json.dump(metadata, f, indent=2)
    
print(f"  ✓ Metadata saved: {metadata_path}")

print()
print("="*70)
print("NEXT STEPS:")
print("="*70)
print("""
1. In injury_risk_logistic_regression.ipynb, add at the end:
   
   import joblib
   joblib.dump(model, '../models/injury_model.pkl')
   joblib.dump(scaler, '../models/injury_scaler.pkl')
   print("Injury model and scaler saved!")

2. In Final Performance Model/Performance_Model_Baseline.ipynb, add at the end:
   
   import joblib
   joblib.dump(model, '../models/performance_model.pkl')
   joblib.dump(scaler, '../models/performance_scaler.pkl')
   print("Performance model and scaler saved!")

3. Run both notebooks to completion, then run this script again:
   
   python save_models.py

4. Verify all files are saved in the models/ directory
""")

print()
print("="*70)
print("MODELS DIRECTORY CONTENTS:")
print("="*70 + "\n")

if os.path.exists("models"):
    for root, dirs, files in os.walk("models"):
        level = root.replace("models", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath) / 1024
            print(f"{subindent}📄 {file} ({size:.2f} KB)")
else:
    print("  Models directory does not exist yet.")

print()
