"""
src/ package — Core application logic for athlete analytics pipeline

Contains all business logic modules:
- db_utils.py: Snowflake database operations
- injury_predictor.py: Injury risk prediction model
- performance_scorer.py: Player performance scoring
- genai_recommender.py: AI-powered recommendations (OpenAI + rule-based)
- athlete_pipeline.py: Standalone batch pipeline orchestration

These modules are used by both:
1. Standalone scripts (src/athlete_pipeline.py)
2. Airflow DAG tasks (dags/tasks/)
"""

__all__ = [
    "db_utils",
    "injury_predictor",
    "performance_scorer",
    "genai_recommender",
    "athlete_pipeline",
]
