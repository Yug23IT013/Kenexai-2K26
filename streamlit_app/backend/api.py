"""
FastAPI Backend for Athlete Analytics Platform
===============================================
Handles Snowflake queries, Groq AI integration, and model connections.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import pandas as pd
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL
from dotenv import load_dotenv
from groq import Groq
import logging

load_dotenv()

# ─────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SNOWFLAKE_CONFIG = {
    "account":   os.getenv("SNOWFLAKE_ACCOUNT", "your_snowflake_account_here"),
    "user":      os.getenv("SNOWFLAKE_USER", "MARK"),
    "password":  os.getenv("SNOWFLAKE_PASSWORD"),
    "database":  os.getenv("SNOWFLAKE_DATABASE", "sports_db"),
    "schema":    os.getenv("SNOWFLAKE_SCHEMA", "analytics"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "sports_wh"),
    "role":      os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
}

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ─────────────────────────────────────────────────────────────────
# FASTAPI SETUP
# ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Athlete Analytics Backend",
    description="API for predictions, recommendations, and AI chat",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────────────────────────────

def get_snowflake_connection():
    """Get Snowflake database connection."""
    try:
        engine = create_engine(URL(**SNOWFLAKE_CONFIG))
        return engine
    except Exception as e:
        logger.error(f"Snowflake connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


# ─────────────────────────────────────────────────────────────────
# GROQ AI INTEGRATION
# ─────────────────────────────────────────────────────────────────

groq_client = Groq(api_key=GROQ_API_KEY)

# List of available models to try in order
AVAILABLE_MODELS = [
    "llama-3.2-90b-vision-preview",
    "llama-3.2-11b-vision-preview",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]

def get_working_model():
    """Find a working model from available options."""
    for model in AVAILABLE_MODELS:
        try:
            groq_client.chat.completions.create(
                messages=[{"role": "user", "content": "test"}],
                model=model,
                max_tokens=1,
            )
            logger.info(f"✓ Using Groq model: {model}")
            return model
        except:
            continue
    return "llama-3.2-11b-vision-preview"  # Default fallback

GROQ_MODEL = get_working_model()

def generate_response_with_groq(system_prompt: str, user_message: str, model: Optional[str] = None) -> str:
    """Generate response using Groq API."""
    try:
        if model is None:
            model = GROQ_MODEL
        
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=model,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error with model {model}: {e}")
        # Fallback to a simple response if Groq fails
        return f"Analysis of '{user_message[:50]}...': The query has been received and forwarded to our system."


# ─────────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────────────────────────

class PlayerPrediction(BaseModel):
    player_id: int
    player_name: str
    team_long_name: str
    performance_score: float
    injury_risk_label: str
    injury_risk_prob: float
    ai_recommendations: str
    prediction_timestamp: str


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict] = None
    role: str = "coach"  # coach or player


class ChatResponse(BaseModel):
    response: str
    generated_query: Optional[str] = None
    data: Optional[List[Dict]] = None


class QueryRequest(BaseModel):
    natural_language_query: str
    execute: bool = False


class AthletePrediction(BaseModel):
    player_id: int
    player_name: str
    performance_score: float
    injury_risk_score: float
    overall_risk_level: str
    recommended_action: str


# ─────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Athlete Analytics Backend"}


# ─────────────────────────────────────────────────────────────────
# PLAYER PREDICTIONS ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@app.get("/predictions/player/{player_id}")
def get_player_prediction(player_id: int):
    """Get latest prediction for a player."""
    try:
        engine = get_snowflake_connection()
        query = f"""
            SELECT
                po.player_id,
                po.player_name,
                ti.team_long_name,
                po.performance_score,
                po.injury_risk_label,
                po.injury_risk_prob,
                po.ai_recommendations,
                po.prediction_timestamp
            FROM predictions_output po
            JOIN player_injury pi ON po.player_id = pi.player_id
            JOIN team_info ti ON pi.team_id = ti.team_id
            WHERE po.player_id = {player_id}
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY po.player_id ORDER BY po.prediction_timestamp DESC
            ) = 1
        """
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Player prediction not found")
        
        row = df.iloc[0]
        return {
            "player_id": int(row["player_id"]),
            "player_name": str(row["player_name"]),
            "team": str(row["team_long_name"]),
            "performance_score": float(row["performance_score"]),
            "injury_risk_label": str(row["injury_risk_label"]),
            "injury_risk_prob": float(row["injury_risk_prob"]),
            "recommendations": str(row["ai_recommendations"]),
            "timestamp": str(row["prediction_timestamp"])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/all")
def get_all_predictions(limit: int = 50, risk_level: Optional[str] = None):
    """Get all or filtered predictions."""
    try:
        engine = get_snowflake_connection()
        
        query = """
            SELECT
                po.player_id,
                po.player_name,
                ti.team_long_name,
                po.performance_score,
                po.injury_risk_label,
                po.injury_risk_prob
            FROM predictions_output po
            JOIN player_injury pi ON po.player_id = pi.player_id
            JOIN team_info ti ON pi.team_id = ti.team_id
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY po.player_id ORDER BY po.prediction_timestamp DESC
            ) = 1
        """
        
        if risk_level:
            query += f" WHERE po.injury_risk_label = '{risk_level}'"
        
        query += f" ORDER BY po.injury_risk_prob DESC LIMIT {limit}"
        
        df = pd.read_sql(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error fetching predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# AI CHAT ENDPOINTS WITH GROQ
# ─────────────────────────────────────────────────────────────────

@app.post("/chat/query")
def chat_query(request: ChatRequest) -> ChatResponse:
    """
    Process natural language query and generate response with Groq.
    Optionally queries Snowflake if SQL is generated.
    """
    try:
        role = request.role
        message = request.message
        
        # Define role-specific system prompt
        if role == "coach":
            system_prompt = """You are an expert sports analytics assistant helping coaches manage player health and performance.
Your role is to:
1. Answer questions about player performance, injury risk, and recommendations
2. Generate safe, read-only SQL queries for athlete data when needed
3. Analyze trends and provide actionable coaching insights
4. Always recommend consulting medical staff for injury-related decisions

When a coach asks for data, generate a SQL query if appropriate. Return it in <SQL>...</SQL> tags.
Keep responses concise and actionable."""
        else:
            system_prompt = """You are a personal sports performance coach assisting athletes.
Your role is to:
1. Provide personalized performance insights
2. Explain injury risk factors and recovery recommendations
3. Suggest training adjustments based on current metrics
4. Motivate and encourage healthy decisions

Keep responses supportive, informative, and personalized."""
        
        # Generate response with Groq
        groq_response = generate_response_with_groq(system_prompt, message)
        
        # Extract SQL if present (optional)
        generated_sql = None
        if "<SQL>" in groq_response and "</SQL>" in groq_response:
            generated_sql = groq_response.split("<SQL>")[1].split("</SQL>")[0].strip()
        
        return ChatResponse(
            response=groq_response,
            generated_query=generated_sql,
            data=None
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/query-with-data")
def chat_query_with_data(request: ChatRequest) -> ChatResponse:
    """
    Process query, generate SQL via Groq, execute it, and provide AI analysis.
    """
    try:
        message = request.message
        
        # Step 1: Ask Groq to generate SQL
        sql_prompt = f"""Based on this coaching query: "{message}"
        
Generate a safe, read-only SQL query to fetch relevant athlete data from Snowflake.

Tables available:
- athlete_predictions (player_id, player_name, performance_score, injury_risk_prob, injury_risk_label, recommended_action)
- player_injury (player_id, fatigue_index, training_load, recovery_time, previous_injury)
- team_info (team_id, team_long_name)

Return ONLY the SQL query, no explanation."""
        
        sql_response = generate_response_with_groq(
            "You are a Snowflake SQL expert. Generate safe read-only queries.",
            sql_prompt
        )
        
        generated_sql = sql_response.strip()
        
        # Step 2: Execute SQL if valid
        data = None
        if "SELECT" in generated_sql.upper() and "DROP" not in generated_sql.upper():
            engine = get_snowflake_connection()
            df = pd.read_sql(generated_sql, engine)
            data = df.to_dict(orient="records") if not df.empty else []
        
        # Step 3: Generate AI analysis
        analysis_prompt = f"""Query: {message}
        
Data retrieved (first 5 rows):
{data[:5] if data else "No data"}

Provide a coaching-friendly analysis of this data."""
        
        analysis = generate_response_with_groq(
            "You are a sports analytics expert providing coaching insights.",
            analysis_prompt
        )
        
        return ChatResponse(
            response=analysis,
            generated_query=generated_sql,
            data=data
        )
    except Exception as e:
        logger.error(f"Query with data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# PLAYER DETAILS ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@app.get("/player/{player_id}/stats")
def get_player_stats(player_id: int):
    """Get player skill stats."""
    try:
        engine = get_snowflake_connection()
        query = f"""
            SELECT
                player_name,
                potential,
                ball_control,
                dribbling,
                stamina,
                reactions,
                balance,
                strength,
                acceleration,
                age
            FROM player_stats
            WHERE player_id = {player_id}
            LIMIT 1
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return df.iloc[0].to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/player/{player_id}/injury-details")
def get_player_injury_details(player_id: int):
    """Get player injury and load metrics."""
    try:
        engine = get_snowflake_connection()
        query = f"""
            SELECT
                player_id,
                fatigue_index,
                training_load,
                recovery_time,
                minutes_played,
                matches_last_7_days,
                previous_injury
            FROM player_injury
            WHERE player_id = {player_id}
            LIMIT 1
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return {"error": "No injury data found"}
        
        return df.iloc[0].to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# TEAM OVERVIEW ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@app.get("/team/overview")
def get_team_overview():
    """Get team-wide statistics."""
    try:
        engine = get_snowflake_connection()
        query = """
            SELECT
                ti.team_long_name,
                COUNT(DISTINCT ps.player_id) AS player_count,
                ROUND(AVG(po.performance_score), 1) AS avg_performance,
                SUM(CASE WHEN po.injury_risk_label = 'High' THEN 1 ELSE 0 END) AS high_risk_count,
                SUM(CASE WHEN po.injury_risk_label = 'Medium' THEN 1 ELSE 0 END) AS medium_risk_count,
                SUM(CASE WHEN po.injury_risk_label = 'Low' THEN 1 ELSE 0 END) AS low_risk_count
            FROM team_info ti
            LEFT JOIN player_stats ps ON ti.team_id = ps.team_id
            LEFT JOIN predictions_output po ON ps.player_id = po.player_id
            GROUP BY ti.team_long_name
            ORDER BY avg_performance DESC
        """
        df = pd.read_sql(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# GROQ AI INSIGHTS ENDPOINT
# ─────────────────────────────────────────────────────────────────

@app.post("/insights/generate")
def generate_insights(player_id: int):
    """Generate AI-powered insights for a player."""
    try:
        # Get player prediction
        engine = get_snowflake_connection()
        pred_query = f"""
            SELECT * FROM predictions_output
            WHERE player_id = {player_id}
            QUALIFY ROW_NUMBER() OVER (ORDER BY prediction_timestamp DESC) = 1
        """
        pred_df = pd.read_sql(pred_query, engine)
        
        if pred_df.empty:
            raise HTTPException(status_code=404, detail="Player not found")
        
        pred_data = pred_df.iloc[0].to_dict()
        
        # Generate insights with Groq
        insight_prompt = f"""
Analyze this athlete's profile and generate 3 key coaching insights:

Performance Score: {pred_data.get('performance_score', 0)}/100
Injury Risk: {pred_data.get('injury_risk_label', 'Unknown')} ({pred_data.get('injury_risk_prob', 0)*100:.1f}%)
Recommended Action: {pred_data.get('recommended_action', 'Continue monitoring')}

Provide actionable, specific coaching insights based on this data."""
        
        insights = generate_response_with_groq(
            "You are a professional athlete performance coach.",
            insight_prompt
        )
        
        return {
            "player_id": player_id,
            "insights": insights,
            "data": pred_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
