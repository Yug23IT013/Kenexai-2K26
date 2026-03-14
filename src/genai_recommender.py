import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Set to True to use OpenAI API, False to use rule-based templates
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))


def _build_prompt(row: pd.Series) -> str:
    return f"""
You are a professional sports coach analyst. Based on the following player data,
generate a short, specific coaching recommendation (3–4 sentences max).
Focus on injury prevention, training load management, and performance improvement.

Player: {row['player_name']}
Team: {row.get('team_long_name', 'Unknown')}
Age: {row.get('age', 'N/A')}
Performance Score: {row.get('performance_score', 'N/A')}/100
Injury Risk: {row.get('injury_risk_label', 'N/A')} ({row.get('injury_risk_prob', 0)*100:.0f}%)
Fatigue Index: {row.get('fatigue_index', 'N/A')}
Training Load: {row.get('training_load', 'N/A')}
Minutes Played (recent): {row.get('minutes_played', 'N/A')}
Previous Injury: {'Yes' if row.get('previous_injury', 0) == 1 else 'No'}
Matches Last 7 Days: {row.get('matches_last_7_days', 'N/A')}

Provide a concise recommendation for the coaching staff.
""".strip()


def _openai_recommend(row: pd.Series) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional sports performance analyst."},
                {"role": "user",   "content": _build_prompt(row)},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [WARN] OpenAI call failed for {row['player_name']}: {e}. Using fallback.")
        return _rule_based_recommend(row)


def _rule_based_recommend(row: pd.Series) -> str:
    """
    Template-based fallback when OpenAI is not available.
    Uses injury risk label + fatigue to generate sensible text.
    """
    name    = row.get("player_name", "The player")
    risk    = row.get("injury_risk_label", "Low")
    fatigue = row.get("fatigue_index", 0)
    load    = row.get("training_load", 0)
    perf    = row.get("performance_score", 0)
    prev    = row.get("previous_injury", 0)

    if risk == "High":
        rec = (
            f"{name} is at HIGH injury risk with a fatigue index of {fatigue:.1f} "
            f"and training load of {load:.1f}. Immediate rest of at least 48–72 hours is recommended. "
            f"Reduce training intensity by 40% and schedule a physiotherapy assessment. "
        )
        if prev:
            rec += "Given prior injury history, extra precaution is advised before returning to full training."
    elif risk == "Medium":
        rec = (
            f"{name} shows moderate injury risk (fatigue: {fatigue:.1f}). "
            f"Monitor workload closely and limit high-intensity drills this week. "
            f"Recommend active recovery sessions and ensure 8+ hours of sleep. "
        )
        if perf < 50:
            rec += "Performance score is below average — consider tactical role adjustment."
    else:
        rec = (
            f"{name} is in good condition with low injury risk. "
            f"Current training load of {load:.1f} is sustainable. "
            f"Focus on maintaining fitness levels and refining technical skills. "
        )
        if perf >= 75:
            rec += "Strong performance score — consider increased match responsibilities."

    return rec


def generate_recommendations(df: pd.DataFrame) -> pd.Series:
    """
    Takes the merged predictions dataframe and generates a
    coaching recommendation string for each player.

    Args:
        df: DataFrame with columns — player_name, team_long_name, age,
            performance_score, injury_risk_label, injury_risk_prob,
            fatigue_index, training_load, minutes_played,
            previous_injury, matches_last_7_days

    Returns:
        pd.Series of recommendation strings (same index as df)
    """
    print(f"  Generating recommendations for {len(df)} players...")

    if USE_OPENAI:
        print("  Using OpenAI GPT for recommendations.")
        recommendations = df.apply(_openai_recommend, axis=1)
    else:
        print("  Using rule-based recommendations (no OpenAI key found).")
        recommendations = df.apply(_rule_based_recommend, axis=1)

    print("  Recommendations generated.")
    return recommendations