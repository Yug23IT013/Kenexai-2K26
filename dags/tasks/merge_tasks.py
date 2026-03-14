"""
Merge Tasks
===========
Combine injury risk and performance predictions.
Compatible with output from src/injury_predictor and src/performance_scorer.
"""

import pandas as pd
from airflow.utils.log.logging_mixin import LoggingMixin


logger = LoggingMixin().log


def merge_model_results(injury_file: str, performance_file: str, output_file: str, **context):
    """
    Merge injury and performance model predictions.
    Handles flexible column names from src/ modules.
    
    Args:
        injury_file: Path to injury predictions CSV (from src/injury_predictor.py)
        performance_file: Path to performance predictions CSV (from src/performance_scorer.py)
        output_file: Path to save merged results CSV
    """
    
    logger.info("Merging model predictions...")
    
    try:
        # Load predictions from both models
        injury_df = pd.read_csv(injury_file)
        performance_df = pd.read_csv(performance_file)
        
        logger.info(f"Loaded {len(injury_df)} injury predictions")
        logger.info(f"Loaded {len(performance_df)} performance predictions")
        logger.info(f"Injury columns: {list(injury_df.columns)}")
        logger.info(f"Performance columns: {list(performance_df.columns)}")
        
        # Identify the risk score column (can be injury_risk_prob or injury_risk_score)
        risk_col = "injury_risk_prob" if "injury_risk_prob" in injury_df.columns else "injury_risk_score"
        score_col = "performance_score" if "performance_score" in performance_df.columns else "predicted_rating"
        
        # Select relevant columns for merge
        injury_subset = injury_df[["player_id", "player_name", "team_long_name", 
                                    risk_col, "injury_risk_label"]].copy()
        performance_subset = performance_df[["player_id", score_col]].copy()
        
        # Rename for consistency
        injury_subset.rename(columns={risk_col: "injury_risk_score"}, inplace=True)
        performance_subset.rename(columns={score_col: "performance_score"}, inplace=True)
        
        # Merge on player_id
        merged = injury_subset.merge(
            performance_subset,
            on="player_id",
            how="inner"
        )
        
        logger.info(f"Merged {len(merged)} player records")
        
        # Create composite risk score (combine injury risk with performance drop)
        merged["performance_risk_score"] = 1.0 - (merged["performance_score"] / 100.0)
        
        # Weighted composite risk (70% injury risk, 30% performance risk)
        merged["composite_risk_score"] = (
            0.7 * merged["injury_risk_score"] + 
            0.3 * merged["performance_risk_score"]
        )
        
        # Overall risk classification
        merged["overall_risk_level"] = pd.cut(
            merged["composite_risk_score"],
            bins=[0, 0.3, 0.6, 1.0],
            labels=["Low Risk", "Medium Risk", "High Risk"]
        )
        
        # Priority ranking
        merged["priority_rank"] = merged["composite_risk_score"].rank(ascending=False)
        
        # Save merged results
        merged.to_csv(output_file, index=False)
        logger.info(f"Merged results saved to {output_file}")
        
        # Log summary statistics
        logger.info(f"High Risk players: {len(merged[merged['overall_risk_level'] == 'High Risk'])}")
        logger.info(f"Medium Risk players: {len(merged[merged['overall_risk_level'] == 'Medium Risk'])}")
        logger.info(f"Low Risk players: {len(merged[merged['overall_risk_level'] == 'Low Risk'])}")
        
        # Push to XCom
        context["task_instance"].xcom_push(key="merged_results", value=output_file)
        
        return {
            "status": "success",
            "total_players": len(merged),
            "high_risk_count": int(len(merged[merged['overall_risk_level'] == 'High Risk'])),
            "medium_risk_count": int(len(merged[merged['overall_risk_level'] == 'Medium Risk'])),
            "low_risk_count": int(len(merged[merged['overall_risk_level'] == 'Low Risk'])),
            "output_file": output_file
        }
        
    except Exception as e:
        logger.error(f"Error merging predictions: {str(e)}")
        raise
