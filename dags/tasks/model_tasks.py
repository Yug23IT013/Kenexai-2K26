"""
Model Inference Tasks
=====================
Run trained models using src/injury_predictor.py and src/performance_scorer.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
from airflow.utils.log.logging_mixin import LoggingMixin

# Add src/ to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from injury_predictor import predict_injury_risk
from performance_scorer import compute_performance_score

logger = LoggingMixin().log


def run_injury_model(input_file: str, model_path: str = None, scaler_path: str = None, output_file: str = "/tmp/injury_predictions.csv", **context):
    """
    Run injury risk prediction using src/injury_predictor.py.
    
    Args:
        input_file: Path to input player data CSV
        model_path: Unused (for compatibility)
        scaler_path: Unused (for compatibility)
        output_file: Path to save predictions CSV
    """
    
    logger.info("Running injury risk prediction model...")
    
    try:
        # Load data
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} player records")
        
        # Use src/injury_predictor.py to get predictions
        results = predict_injury_risk(df)
        logger.info(f"Injury predictions: {len(results[results['injury_risk_label'] == 'High'])} high-risk players")
        
        # Save predictions
        results.to_csv(output_file, index=False)
        logger.info(f"Injury predictions saved to {output_file}")
        
        # Push to XCom
        context["task_instance"].xcom_push(key="injury_results", value=output_file)
        
        return {
            "status": "success",
            "predictions_made": len(results),
            "at_risk_players": len(results[results['injury_risk_label'] == 'High']),
            "output_file": output_file
        }
        
    except Exception as e:
        logger.error(f"Error running injury model: {str(e)}")
        raise


def run_performance_model(input_file: str, model_path: str = None, scaler_path: str = None, output_file: str = "/tmp/performance_predictions.csv", **context):
    """
    Run performance prediction using src/performance_scorer.py.
    
    Args:
        input_file: Path to input player data CSV
        model_path: Unused (for compatibility)
        scaler_path: Unused (for compatibility)
        output_file: Path to save predictions CSV
    """
    
    logger.info("Running performance prediction model...")
    
    try:
        # Load data
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} player records")
        
        # Use src/performance_scorer.py to compute scores
        results = compute_performance_score(df)
        
        logger.info(f"Average predicted performance: {results['performance_score'].mean():.2f}")
        
        # Save predictions
        results.to_csv(output_file, index=False)
        logger.info(f"Performance predictions saved to {output_file}")
        
        # Push to XCom
        context["task_instance"].xcom_push(key="performance_results", value=output_file)
        
        return {
            "status": "success",
            "predictions_made": len(results),
            "avg_predicted_score": float(results['performance_score'].mean()),
            "output_file": output_file
        }
        
    except Exception as e:
        logger.error(f"Error running performance model: {str(e)}")
        raise
