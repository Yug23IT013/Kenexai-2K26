"""
Snowflake Tasks
===============
Write predictions and recommendations to Snowflake for analytics.
"""

import pandas as pd
from snowflake.connector import connect
from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.models import Variable


logger = LoggingMixin().log


def write_results_to_snowflake(input_file: str, table_name: str, database: str, schema: str, **context):
    """
    Write predictions and recommendations to Snowflake table.
    
    Args:
        input_file: Path to recommendations CSV
        table_name: Target table name in Snowflake
        database: Snowflake database name
        schema: Snowflake schema name
    """
    
    logger.info(f"Writing results to Snowflake ({database}.{schema}.{table_name})...")
    
    try:
        # Load recommendations
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} records to write")
        
        # Connect to Snowflake
        conn = connect(
            account="your_snowflake_account_here",
            user="MARK",
            password=Variable.get("snowflake_password", default_var=""),
            warehouse="SPORTS_WH",
            database=database,
            schema=schema,
            role="ACCOUNTADMIN"
        )
        
        # Prepare data for insertion
        df_insert = df[[
            "player_id",
            "player_name",
            "position",
            "injury_prediction",
            "injury_risk_score",
            "injury_risk_level",
            "predicted_rating",
            "current_rating",
            "rating_improvement",
            "composite_risk_score",
            "overall_risk_level",
            "priority_rank",
            "action_required",
            "recommended_action",
            "ai_recommendations"
        ]].copy()
        
        # Add timestamp
        from datetime import datetime
        df_insert["prediction_timestamp"] = datetime.now()
        
        # Write using cursor
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
            player_id INTEGER,
            player_name VARCHAR,
            position VARCHAR,
            injury_prediction INTEGER,
            injury_risk_score FLOAT,
            injury_risk_level VARCHAR,
            predicted_rating FLOAT,
            current_rating FLOAT,
            rating_improvement FLOAT,
            composite_risk_score FLOAT,
            overall_risk_level VARCHAR,
            priority_rank FLOAT,
            action_required VARCHAR,
            recommended_action VARCHAR,
            ai_recommendations VARCHAR,
            prediction_timestamp TIMESTAMP_NTZ
        );
        """
        
        cursor.execute(create_table_sql)
        logger.info(f"Table {table_name} created/verified")
        
        # Insert records using multi-row insert
        insert_sql = f"""
        INSERT INTO {schema}.{table_name} VALUES
        """
        
        for idx, row in df_insert.iterrows():
            values = (
                int(row["player_id"]),
                f"'{row['player_name']}'",
                f"'{row['position']}'",
                int(row["injury_prediction"]),
                float(row["injury_risk_score"]),
                f"'{row['injury_risk_level']}'",
                float(row["predicted_rating"]),
                float(row["current_rating"]),
                float(row["rating_improvement"]),
                float(row["composite_risk_score"]),
                f"'{row['overall_risk_level']}'",
                float(row["priority_rank"]),
                f"'{row['action_required']}'",
                f"'{row['recommended_action']}'",
                f"'{str(row['ai_recommendations'][:500])}'",  # Truncate long text
                f"'{row['prediction_timestamp']}'"
            )
            
            if idx == 0:
                insert_sql += f"\n({', '.join(str(v) for v in values)})"
            else:
                insert_sql += f",\n({', '.join(str(v) for v in values)})"
        
        insert_sql += ";"
        
        cursor.execute(insert_sql)
        conn.commit()
        
        logger.info(f"Successfully wrote {len(df_insert)} records to {table_name}")
        
        # Verify count
        verify_sql = f"SELECT COUNT(*) FROM {schema}.{table_name};"
        cursor.execute(verify_sql)
        count = cursor.fetchone()[0]
        logger.info(f"Table now contains {count} total records")
        
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "rows_written": len(df_insert),
            "total_records_in_table": count,
            "table": f"{database}.{schema}.{table_name}"
        }
        
    except Exception as e:
        logger.error(f"Error writing to Snowflake: {str(e)}")
        raise
