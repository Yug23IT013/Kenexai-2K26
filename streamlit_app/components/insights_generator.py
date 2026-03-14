"""
Generate AI insights using Groq API for player and team data.
Designed for scalability with summarized context instead of raw data.
"""

import streamlit as st
from groq import Groq
from typing import Dict, Optional

GROQ_API_KEY = "your_groq_api_key_here"


def _get_groq_client():
    """Create and return a Groq client instance."""
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        raise Exception(f"Failed to initialize Groq client: {str(e)}")


def generate_player_insights(player_data: Dict) -> str:
    """
    Generate AI insights for a player using summarized context.
    
    Args:
        player_data: Dictionary with player info (name, stats, performance, injury risk)
    
    Returns:
        AI-generated insights string
    """
    
    try:
        client = _get_groq_client()
        
        # Prepare summarized context for scalability
        context = f"""
Player Profile Summary:
- Name: {player_data.get('player_name', 'Unknown')}
- Age: {player_data.get('age', 'N/A')}
- Team: {player_data.get('team_long_name', 'N/A')}
- Potential: {player_data.get('potential', 'N/A')}

Performance Metrics:
- Performance Score: {player_data.get('performance_score', 0):.1f}/100
- Injury Risk Level: {player_data.get('injury_risk_label', 'N/A')}
- Injury Risk Probability: {player_data.get('injury_risk_prob', 0):.1f}%

Key Attributes:
- Ball Control: {player_data.get('ball_control', 'N/A')}
- Dribbling: {player_data.get('dribbling', 'N/A')}
- Stamina: {player_data.get('stamina', 'N/A')}
- Reactions: {player_data.get('reactions', 'N/A')}
- Strength: {player_data.get('strength', 'N/A')}
- Defense: {player_data.get('defending', 'N/A')}

Workload Indicators:
- Minutes Played: {player_data.get('minutes_played', 'N/A')}
- Matches Played: {player_data.get('matches_played', 'N/A')}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": """You are a professional football analytics expert. 
Analyze the player profile data and provide concise, actionable insights about:
1. Current performance status
2. Injury risk assessment and recommendations
3. Key strengths and areas for improvement
4. Training suggestions based on metrics

Keep response to 3-4 sentences, maximum 150 words. Be specific and data-driven."""
                },
                {
                    "role": "user",
                    "content": f"Analyze this player and provide insights:\n{context}"
                }
            ],
            temperature=0.7,
            max_tokens=200
        )

        if response and response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            return "Error: No response from AI model. Please try again."

    except Exception as e:
        error_str = str(e).lower()
        # More specific error handling
        if "authentication" in error_str or "unauthorized" in error_str or "invalid_api_key" in error_str:
            return "❌ Authentication Error: Invalid Groq API key. Please verify the API key is correct."
        elif "timeout" in error_str:
            return "⏱️ Request timed out. The AI service is taking too long. Please try again."
        elif "connection" in error_str:
            return "🔌 Connection error: Unable to reach the Groq service. Please check your internet."
        elif "rate_limit" in error_str or "quota" in error_str:
            return "⚠️ Rate limit exceeded. Please wait a moment and try again."
        else:
            return f"❌ Error: {str(e)[:100]}"



def generate_team_insights(team_summary: Dict) -> str:
    """
    Generate AI insights for a team using aggregated statistics.
    Designed for scalability - uses team-level summaries instead of individual data.
    
    Args:
        team_summary: Dictionary with aggregated team data
    
    Returns:
        AI-generated team insights string
    """
    
    try:
        client = _get_groq_client()
        
        # Prepare aggregated context for scalability (no individual player details)
        context = f"""
Team Performance Summary:
- Team Name: {team_summary.get('team_long_name', 'Unknown')}
- Total Players: {team_summary.get('total_players', 0)}

Overall Metrics:
- Average Performance Score: {team_summary.get('avg_performance', 0):.1f}/100
- Min Performance: {team_summary.get('min_performance', 0):.1f}/100
- Max Performance: {team_summary.get('max_performance', 0):.1f}/100

Squad Health Assessment:
- High Risk Players: {int(team_summary.get('high_risk_players', 0))}
- Medium Risk Players: {int(team_summary.get('medium_risk_players', 0))}
- Low Risk Players: {int(team_summary.get('low_risk_players', 0))}
- High Risk Percentage: {(int(team_summary.get('high_risk_players', 0)) / team_summary.get('total_players', 1)) * 100:.1f}%

Performance Distribution:
- Top Performers (>80): {int(team_summary.get('high_performers', 0))} players
- Mid Tier (50-80): {int(team_summary.get('mid_performers', 0))} players
- Below Average (<50): {int(team_summary.get('low_performers', 0))} players
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": """You are a professional football team analyst and coach. 
Analyze the team statistics and provide strategic insights about:
1. Overall team health and performance status
2. Injury risk concerns and squad depth assessment
3. Team strengths and weaknesses based on performance distribution
4. Recommended focus areas for the next training period

Keep response to 4-5 sentences, maximum 200 words. Focus on actionable team-level strategies."""
                },
                {
                    "role": "user",
                    "content": f"Analyze this team and provide strategic insights:\n{context}"
                }
            ],
            temperature=0.7,
            max_tokens=250
        )

        if response and response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            return "Error: No response from AI model. Please try again."

    except Exception as e:
        error_str = str(e).lower()
        # More specific error handling
        if "authentication" in error_str or "unauthorized" in error_str or "invalid_api_key" in error_str:
            return "❌ Authentication Error: Invalid Groq API key. Please verify the API key is correct."
        elif "timeout" in error_str:
            return "⏱️ Request timed out. The AI service is taking too long. Please try again."
        elif "connection" in error_str:
            return "🔌 Connection error: Unable to reach the Groq service. Please check your internet."
        elif "rate_limit" in error_str or "quota" in error_str:
            return "⚠️ Rate limit exceeded. Please wait a moment and try again."
        else:
            return f"❌ Error: {str(e)[:100]}"
