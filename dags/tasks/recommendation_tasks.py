"""
Recommendation Tasks
====================
Generate AI-powered recommendations using src/genai_recommender.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
from airflow.utils.log.logging_mixin import LoggingMixin

# Add src/ to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from genai_recommender import generate_recommendations as src_generate_recommendations

logger = LoggingMixin().log


def generate_recommendations(input_file: str, output_file: str = "/tmp/recommendations.csv", **context):
    """
    Generate AI-powered recommendations using src/genai_recommender.py.
    Uses OpenAI if available, otherwise rule-based recommendations.
    
    Args:
        input_file: Path to merged predictions CSV (from merge_results task)
        output_file: Path to save recommendations CSV
    """
    
    logger.info("Generating AI-powered recommendations...")
    
    try:
        # Load merged predictions
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} player records")
        
        # Use src/genai_recommender to generate recommendations
        # This supports both OpenAI and rule-based fallback
        recommendations = src_generate_recommendations(df)
        
        # Add recommendations to dataframe
        df["ai_recommendations"] = recommendations.values
        
        # Create action priority based on injury risk (simplified classification)
        df["action_required"] = df.apply(
            lambda row: "Immediate Action" if row.get("injury_risk_prob", 0) > 0.7 
                        else "Monitor" if row.get("injury_risk_prob", 0) > 0.4 
                        else "No Action",
            axis=1
        )
        
        # Save with recommendations
        df.to_csv(output_file, index=False)
        logger.info(f"Recommendations saved to {output_file}")
        
        # Log action summary
        action_counts = df["action_required"].value_counts()
        logger.info(f"Summary - {dict(action_counts.to_dict())}")
        
        # Push to XCom
        context["task_instance"].xcom_push(key="recommendations", value=output_file)
        
        return {
            "status": "success",
            "total_recommendations": len(recommendations),
            "output_file": output_file
        }
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise
