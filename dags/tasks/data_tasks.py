"""
Data Fetching Tasks
====================
Fetch player data from Snowflake using src/db_utils.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
from airflow.utils.log.logging_mixin import LoggingMixin

# Add src/ to path so we can import db_utils
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from db_utils import fetch_player_injury_features, fetch_player_stats_features, fetch_all_players

logger = LoggingMixin().log


def fetch_player_data(database: str = None, schema: str = None, output_file: str = "/tmp/player_data.csv", **context):
    """
    Fetch player data from Snowflake using src/db_utils functions.
    Combines injury and stats features into a single file.
    
    Args:
        database: Unused (for compatibility)
        schema: Unused (for compatibility)
        output_file: Path to save the merged player data CSV
    """
    
    logger.info("Fetching player data from Snowflake...")
    
    try:
        # Fetch injury features (includes all injury-relevant data)
        logger.info("Fetching injury features...")
        injury_df = fetch_player_injury_features()
        logger.info(f"Fetched {len(injury_df)} injury records")
        
        # Fetch stats features (includes performance-relevant data)
        logger.info("Fetching stats features...")
        stats_df = fetch_player_stats_features()
        logger.info(f"Fetched {len(stats_df)} stats records")
        
        # Merge on player_id
        df = injury_df.merge(
            stats_df,
            on=["player_id", "player_name", "team_long_name"],
            how="inner"
        )
        
        logger.info(f"Merged into {len(df)} combined player records")
        
        # Save to temporary file
        df.to_csv(output_file, index=False)
        logger.info(f"Data saved to {output_file}")
        
        # Push data path to XCom for downstream tasks
        context["task_instance"].xcom_push(key="player_data_path", value=output_file)
        
        return {
            "status": "success",
            "rows_fetched": len(df),
            "output_file": output_file
        }
        
    except Exception as e:
        logger.error(f"Error fetching player data: {str(e)}")
        raise
