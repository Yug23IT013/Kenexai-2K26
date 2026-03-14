"""
Athlete Performance Pipeline — Airflow DAG
============================================
Orchestrates the end-to-end ML pipeline for injury risk and performance prediction.

DAG Flow:
    fetch_data
         ├── run_injury_model ──────┐
         └── run_performance_model ─┤
                              merge_results
                                  └── generate_recommendations
                                      ├── write_to_snowflake
                                      └── send_alerts

Schedule: Daily at 6:00 AM UTC
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.models import Variable
from airflow.utils.dates import days_ago

# Import task functions
from tasks.data_tasks import fetch_player_data
from tasks.model_tasks import run_injury_model, run_performance_model
from tasks.merge_tasks import merge_model_results
from tasks.recommendation_tasks import generate_recommendations
from tasks.snowflake_tasks import write_results_to_snowflake
from tasks.alert_tasks import send_performance_alerts


# ─────────────────────────────────────────────────────────────────────
# DAG Configuration
# ─────────────────────────────────────────────────────────────────────

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(0),
    "email_on_failure": True,
    "email_on_retry": False,
    "email": ["admin@example.com"],
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "athlete_performance_pipeline",
    default_args=DEFAULT_ARGS,
    description="End-to-end ML pipeline for injury risk and performance prediction",
    schedule_interval="0 6 * * *",  # Daily at 6:00 AM UTC
    catchup=False,
    tags=["sports-analytics", "ml-pipeline"],
)


# ─────────────────────────────────────────────────────────────────────
# Task Definitions
# ─────────────────────────────────────────────────────────────────────

# Task 1: Fetch player data from Snowflake
task_fetch_data = PythonOperator(
    task_id="fetch_data",
    python_callable=fetch_player_data,
    op_kwargs={
        "database": "sports_db",
        "schema": "analytics",
        "output_file": "/tmp/player_data.csv",
    },
    dag=dag,
)

# Task 2a: Run injury risk prediction model (parallel with performance model)
task_injury_model = PythonOperator(
    task_id="run_injury_model",
    python_callable=run_injury_model,
    op_kwargs={
        "input_file": "/tmp/player_data.csv",
        "output_file": "/tmp/injury_predictions.csv",
    },
    dag=dag,
)

# Task 2b: Run performance prediction model (parallel with injury model)
task_performance_model = PythonOperator(
    task_id="run_performance_model",
    python_callable=run_performance_model,
    op_kwargs={
        "input_file": "/tmp/player_data.csv",
        "output_file": "/tmp/performance_predictions.csv",
    },
    dag=dag,
)

# Task 3: Merge results from both models
task_merge = PythonOperator(
    task_id="merge_results",
    python_callable=merge_model_results,
    op_kwargs={
        "injury_file": "/tmp/injury_predictions.csv",
        "performance_file": "/tmp/performance_predictions.csv",
        "output_file": "/tmp/merged_predictions.csv",
    },
    dag=dag,
)

# Task 4: Generate AI-powered recommendations
task_recommendations = PythonOperator(
    task_id="generate_recommendations",
    python_callable=generate_recommendations,
    op_kwargs={
        "input_file": "/tmp/merged_predictions.csv",
        "output_file": "/tmp/recommendations.csv",
    },
    dag=dag,
)

# Task 5a: Write results to Snowflake (parallel with alerts)
task_write_snowflake = PythonOperator(
    task_id="write_to_snowflake",
    python_callable=write_results_to_snowflake,
    op_kwargs={
        "input_file": "/tmp/recommendations.csv",
        "table_name": "athlete_predictions",
        "database": "sports_db",
        "schema": "analytics",
    },
    dag=dag,
)

# Task 5b: Send alerts for high-risk players (parallel with write_to_snowflake)
task_send_alerts = PythonOperator(
    task_id="send_alerts",
    python_callable=send_performance_alerts,
    op_kwargs={
        "input_file": "/tmp/merged_predictions.csv",
        "injury_threshold": 0.7,
    },
    dag=dag,
)


# ─────────────────────────────────────────────────────────────────────
# DAG Dependencies (Pipeline Flow)
# ─────────────────────────────────────────────────────────────────────

# fetch_data -> [run_injury_model, run_performance_model] -> merge_results
task_fetch_data >> [task_injury_model, task_performance_model]
[task_injury_model, task_performance_model] >> task_merge

# merge_results -> generate_recommendations
task_merge >> task_recommendations

# generate_recommendations -> [write_to_snowflake, send_alerts]
task_recommendations >> [task_write_snowflake, task_send_alerts]


if __name__ == "__main__":
    dag.cli()

