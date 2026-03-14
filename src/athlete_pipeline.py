"""
Athlete Performance Analytics Pipeline
---------------------------------------
Schedule : Daily at 6:00 AM
Flow     : fetch_data → run_injury_model → run_performance_model
                      → merge_results → generate_recommendations
                      → write_to_snowflake → send_alerts

Each task uses XCom to pass DataFrames as JSON between steps.
"""

import sys
import os
import json
from datetime import datetime, timedelta

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

# Make sure Airflow can find your src/ modules
SRC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# ── DAG DEFAULT ARGS ────────────────────────────────────────────
default_args = {
    "owner":            "sports_analytics",
    "depends_on_past":  False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,   # set True and add email if needed
}

# ── TASK FUNCTIONS ──────────────────────────────────────────────

def task_fetch_data(**context):
    """
    Task 1 — Pull latest data from Snowflake.
    Pushes two DataFrames to XCom as JSON strings.
    """
    from db_utils import fetch_player_injury_features, fetch_player_stats_features

    print("Fetching injury features from Snowflake...")
    injury_df = fetch_player_injury_features()
    print(f"  Got {len(injury_df)} rows for injury model.")

    print("Fetching performance features from Snowflake...")
    stats_df = fetch_player_stats_features()
    print(f"  Got {len(stats_df)} rows for performance model.")

    # Push to XCom
    context["ti"].xcom_push(key="injury_df", value=injury_df.to_json(orient="records"))
    context["ti"].xcom_push(key="stats_df",  value=stats_df.to_json(orient="records"))


def task_run_injury_model(**context):
    """
    Task 2 — Load injury_model.pkl and run predictions.
    Reads injury_df from XCom, pushes injury_results.
    """
    from injury_predictor import predict_injury_risk

    raw = context["ti"].xcom_pull(task_ids="fetch_data", key="injury_df")
    injury_df = pd.read_json(raw, orient="records")

    print("Running injury risk model...")
    injury_results = predict_injury_risk(injury_df)

    context["ti"].xcom_push(
        key="injury_results",
        value=injury_results.to_json(orient="records")
    )


def task_run_performance_model(**context):
    """
    Task 3 — Load performance_model.pkl and compute scores.
    Reads stats_df from XCom, pushes performance_results.
    """
    from performance_scorer import compute_performance_score

    raw = context["ti"].xcom_pull(task_ids="fetch_data", key="stats_df")
    stats_df = pd.read_json(raw, orient="records")

    print("Running performance scorer...")
    perf_results = compute_performance_score(stats_df)

    context["ti"].xcom_push(
        key="perf_results",
        value=perf_results.to_json(orient="records")
    )


def task_merge_results(**context):
    """
    Task 4 — Merge injury + performance results on player_id.
    Also pulls extra columns (age, fatigue etc.) for the recommender.
    """
    from db_utils import fetch_all_players

    injury_raw = context["ti"].xcom_pull(task_ids="run_injury_model",       key="injury_results")
    perf_raw   = context["ti"].xcom_pull(task_ids="run_performance_model",  key="perf_results")

    injury_df = pd.read_json(injury_raw, orient="records")
    perf_df   = pd.read_json(perf_raw,   orient="records")

    print("Merging results...")
    merged = injury_df.merge(
        perf_df[["player_id", "performance_score"]],
        on="player_id",
        how="inner"
    )

    # Enrich with extra player context for the recommender
    context_df = fetch_all_players()
    merged = merged.merge(
        context_df[[
            "player_id", "age", "fatigue_index",
            "training_load", "minutes_played",
            "previous_injury"
        ]],
        on="player_id",
        how="left"
    )

    print(f"  Merged {len(merged)} players.")
    context["ti"].xcom_push(key="merged_df", value=merged.to_json(orient="records"))


def task_generate_recommendations(**context):
    """
    Task 5 — Generate coaching recommendation text per player.
    Uses OpenAI if API key is set, otherwise uses rule-based templates.
    """
    from genai_recommender import generate_recommendations

    raw    = context["ti"].xcom_pull(task_ids="merge_results", key="merged_df")
    merged = pd.read_json(raw, orient="records")

    print("Generating coaching recommendations...")
    merged["recommendation"] = generate_recommendations(merged)
    merged["predicted_at"]   = datetime.now().isoformat()

    context["ti"].xcom_push(
        key="final_df",
        value=merged.to_json(orient="records")
    )


def task_write_to_snowflake(**context):
    """
    Task 6 — Write final predictions to predictions_output table.
    """
    from db_utils import write_predictions

    raw      = context["ti"].xcom_pull(task_ids="generate_recommendations", key="final_df")
    final_df = pd.read_json(raw, orient="records")

    # Keep only the columns predictions_output table expects
    output_cols = [
        "player_id", "player_name",
        "performance_score",
        "injury_risk_label", "injury_risk_prob",
        "recommendation", "predicted_at"
    ]
    output_df = final_df[[c for c in output_cols if c in final_df.columns]]

    print("Writing predictions to Snowflake...")
    write_predictions(output_df)


def task_send_alerts(**context):
    """
    Task 7 — Log high-risk players. Extend this to send
    email/Slack/Teams notifications in production.
    """
    raw      = context["ti"].xcom_pull(task_ids="generate_recommendations", key="final_df")
    final_df = pd.read_json(raw, orient="records")

    high_risk = final_df[final_df["injury_risk_label"] == "High"]
    med_risk  = final_df[final_df["injury_risk_label"] == "Medium"]

    print("\n" + "="*50)
    print("PIPELINE SUMMARY")
    print("="*50)
    print(f"  Total players analysed : {len(final_df)}")
    print(f"  High risk players      : {len(high_risk)}")
    print(f"  Medium risk players    : {len(med_risk)}")
    print(f"  Low risk players       : {len(final_df) - len(high_risk) - len(med_risk)}")

    if not high_risk.empty:
        print("\nHIGH RISK PLAYERS — immediate attention needed:")
        for _, row in high_risk.iterrows():
            print(f"  - {row['player_name']} | Risk: {row['injury_risk_prob']*100:.0f}%")

    print("="*50 + "\n")

    # ── Extend here for real notifications ──
    # from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
    # Send a Slack/email message with high_risk.to_string()


# ── DAG DEFINITION ──────────────────────────────────────────────
with DAG(
    dag_id="athlete_performance_pipeline",
    default_args=default_args,
    description="Daily athlete performance scoring and injury risk prediction",
    schedule_interval="0 6 * * *",   # every day at 6:00 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["sports", "ml", "injury", "performance"],
) as dag:

    t1 = PythonOperator(
        task_id="fetch_data",
        python_callable=task_fetch_data,
    )

    t2 = PythonOperator(
        task_id="run_injury_model",
        python_callable=task_run_injury_model,
    )

    t3 = PythonOperator(
        task_id="run_performance_model",
        python_callable=task_run_performance_model,
    )

    t4 = PythonOperator(
        task_id="merge_results",
        python_callable=task_merge_results,
    )

    t5 = PythonOperator(
        task_id="generate_recommendations",
        python_callable=task_generate_recommendations,
    )

    t6 = PythonOperator(
        task_id="write_to_snowflake",
        python_callable=task_write_to_snowflake,
    )

    t7 = PythonOperator(
        task_id="send_alerts",
        python_callable=task_send_alerts,
    )

    # ── PIPELINE FLOW ────────────────────────────────────────────
    # fetch_data
    #     ├── run_injury_model ──┐
    #     └── run_performance_model ─┤
    #                            merge_results
    #                                └── generate_recommendations
    #                                        ├── write_to_snowflake
    #                                        └── send_alerts

    t1 >> [t2, t3] >> t4 >> t5 >> [t6, t7]