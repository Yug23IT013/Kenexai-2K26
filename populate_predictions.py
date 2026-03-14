#!/usr/bin/env python
"""Populate PREDICTIONS_OUTPUT with sample data using bulk insert"""
import os
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()

account = os.getenv('SNOWFLAKE_ACCOUNT')
user = os.getenv('SNOWFLAKE_USER')
password = os.getenv('SNOWFLAKE_PASSWORD')
db = os.getenv('SNOWFLAKE_DATABASE')
schema = os.getenv('SNOWFLAKE_SCHEMA')
warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')

conn = snowflake.connector.connect(
    account=account,
    user=user,
    password=password,
    database=db,
    schema=schema,
    warehouse=warehouse,
)

cursor = conn.cursor()

print('Generating predictions for all players...')

# Create predictions using a single INSERT statement
sql = '''
INSERT INTO PREDICTIONS_OUTPUT (PLAYER_ID, PLAYER_NAME, TEAM_ID, PREDICTED_AT, PERFORMANCE_SCORE, INJURY_RISK, RECOMMENDATION)
SELECT
    ps.PLAYER_ID,
    ps.PLAYER_NAME,
    ps.TEAM_ID,
    CURRENT_TIMESTAMP() as PREDICTED_AT,
    ROUND((ps.OVERALL_RATING * 0.7 + ps.POTENTIAL * 0.2 + (100 - ps.AGE) * 0.1) / 100 * 100, 2) as PERFORMANCE_SCORE,
    ROUND(LEAST(1.0, GREATEST(0.0, 
        (100 - ps.STAMINA) / 100 * 0.4 + 
        (ps.AGE / 40) * 0.4 + 
        (100 - ps.STRENGTH) / 100 * 0.2 +
        COALESCE(pi.FATIGUE_INDEX, 50) / 100 * 0.1
    )), 4) as INJURY_RISK,
    CASE 
        WHEN ((100 - ps.STAMINA) / 100 * 0.4 + (ps.AGE / 40) * 0.4 + (100 - ps.STRENGTH) / 100 * 0.2 + COALESCE(pi.FATIGUE_INDEX, 50) / 100 * 0.1) > 0.7
        THEN 'HIGH RISK: ' || ps.PLAYER_NAME || ' has elevated injury risk. Recommend reduced training load and monitoring.'
        WHEN ((100 - ps.STAMINA) / 100 * 0.4 + (ps.AGE / 40) * 0.4 + (100 - ps.STRENGTH) / 100 * 0.2 + COALESCE(pi.FATIGUE_INDEX, 50) / 100 * 0.1) > 0.5
        THEN 'MEDIUM RISK: ' || ps.PLAYER_NAME || ' shows moderate injury risk. Increase recovery time.'
        ELSE 'LOW RISK: ' || ps.PLAYER_NAME || ' is healthy. Maintain current training status.'
    END as RECOMMENDATION
FROM PLAYER_STATS ps
LEFT JOIN PLAYER_INJURY pi ON ps.PLAYER_ID = pi.PLAYER_ID
'''

try:
    cursor.execute(sql)
    row_count = cursor.rowcount
    conn.commit()
    print(f'✓ Successfully inserted {row_count} predictions into PREDICTIONS_OUTPUT')
except Exception as e:
    print(f'Error: {str(e)[:200]}')
    conn.rollback()

cursor.close()
conn.close()
