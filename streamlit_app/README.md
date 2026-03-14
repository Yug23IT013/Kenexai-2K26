# Football Analytics Platform - Streamlit App & FastAPI Backend

Complete documentation for running the Football Analytics web application with Groq AI integration.

## 📋 Overview

The platform consists of three integrated components:

1. **Streamlit Frontend** - Web UI for coaches and players
2. **FastAPI Backend** - REST API for data and AI operations
3. **Groq AI** - Natural language query processing
4. **Snowflake** - Data warehouse for predictions and player stats

## 🔧 Prerequisites

- Python 3.8+
- pip or conda
- Snowflake account credentials
- Groq API key

## 📦 Installation

### 1. Install Python Dependencies

First, update your main Streamlit environment with required packages:

```bash
pip install streamlit requests python-dotenv
```

Then install backend dependencies:

```bash
pip install -r streamlit_app/backend/requirements.txt
```

Or use the provided startup scripts (see below).

### 2. Configure Environment

Create a `.env` file in `streamlit_app/backend/`:

```bash
# Copy and modify the template
cp streamlit_app/backend/.env.example streamlit_app/backend/.env
# OR create manually with the following:
```

**File: `streamlit_app/backend/.env`**

```env
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_snowflake_account_here
SNOWFLAKE_USER=MARK
SNOWFLAKE_PASSWORD=your_actual_password
SNOWFLAKE_DATABASE=sports_db
SNOWFLAKE_SCHEMA=analytics
SNOWFLAKE_WAREHOUSE=SPORTS_WH

# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Server Configuration
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

⚠️ **Never commit .env to version control. Add it to .gitignore.**

### 3. Verify Snowflake Connection

Test your Snowflake credentials:

```python
import snowflake.connector

conn = snowflake.connector.connect(
    account='your_snowflake_account_here',
    user='MARK',
    password='your_password',
    database='sports_db',
    schema='analytics',
    warehouse='SPORTS_WH'
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM athlete_predictions")
count = cursor.fetchone()[0]
print(f"✓ Connected! Found {count} predictions in database")
cursor.close()
conn.close()
```

## 🚀 Starting the Application

### Option 1: Automated Startup (Recommended)

**On Windows (PowerShell):**

```powershell
# Allow scripts to run (one-time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the startup script
.\streamlit_app\run_app.ps1
```

**On macOS/Linux:**

```bash
chmod +x streamlit_app/run_app.sh
./streamlit_app/run_app.sh
```

**Cross-platform (Python):**

```bash
python streamlit_app/run_app.py
```

### Option 2: Manual Startup

**Terminal 1 - Start FastAPI Backend:**

```bash
cd streamlit_app/backend
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Start Streamlit Frontend:**

```bash
streamlit run streamlit_app/app.py --server.port=8501 --server.address=localhost
```

### Access the Application

- **Streamlit Frontend**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **FastAPI Redoc**: http://localhost:8000/redoc

## 👤 User Accounts

### Coach Accounts

| Username | Password | Role |
|----------|----------|------|
| coach_pep | pass | Coach |
| coach_carlo | pass | Coach |

### Player Accounts

| Username | Password | Role |
|----------|----------|------|
| de_bruyne | pass | Player |
| pedri | pass | Player |
| vinicius | pass | Player |
| haaland | pass | Player |

## 💬 Using the AI Chatbot

### Chatbot Features

The AI assistant in the "Coach Dashboard" → "AI Chatbot" tab uses Groq-powered natural language processing.

#### Simple Queries

Ask the chatbot questions like:

- "Show all high-risk players"
- "What is the team's overall performance?"
- "Who are the top performers this week?"
- "What is De Bruyne's injury risk?"

The backend will:
1. Send your query to Groq API for analysis
2. Generate recommendations or summary

#### Advanced Queries (Query-with-Data)

More complex questions automatically trigger SQL generation:

- "Which players have fatigue above 7?"
- "Compare performance scores across teams"
- "Show players with both high performance and low injury risk"

The backend will:
1. Generate SQL from your natural language question
2. Execute the query on Snowflake
3. Use Groq to analyze and summarize the results
4. Return formatted data and AI insights

### Example Questions

**For Coaches:**

```
"Show me all players with high injury risk"
→ Backend generates: SELECT * FROM athlete_predictions WHERE injury_risk_label = 'High'
→ Groq analyzes and provides: Risk breakdown, recommendations, action items

"Which team has the lowest average performance?"
→ Backend joins team_stats and athlete_predictions
→ Groq provides: Team analysis, improvement suggestions

"Generate a lineup recommendation for tomorrow based on fitness levels"
→ Backend fetches player stats, injury status, recovery metrics
→ Groq generates: AI-powered lineup suggestion with reasoning
```

**For Players:**

```
"What's my current performance score?"
→ Backend fetches personal prediction
→ Groq provides: Analysis, comparison to team average, improvement tips

"What should I do to reduce injury risk?"
→ Backend fetches injury details and load metrics
→ Groq generates: Personalized recovery and prevention recommendations
```

## 🔌 API Endpoints

All endpoints return JSON responses.

### Health Check

```
GET /health
```

Response:
```json
{"status": "healthy", "backend": "FastAPI", "groq": "connected"}
```

### Predictions

```
GET /predictions/player/{player_id}
```

Returns latest prediction for a player:
```json
{
  "player_id": 123,
  "player_name": "De Bruyne",
  "performance_score": 85.3,
  "injury_risk_label": "Low",
  "injury_risk_prob": 0.15,
  "ai_recommendations": "Good recovery status...",
  "prediction_timestamp": "2024-01-15T10:30:00Z"
}
```

```
GET /predictions/all?risk_level=High
```

Returns all predictions filtered by risk level.

### Chat Endpoints

```
POST /chat/query
Content-Type: application/json

{
  "message": "What is the team's avg performance?",
  "role": "coach"
}
```

Response:
```json
{
  "response": "Based on the latest predictions, the team's average performance score is...",
  "query_type": "simple",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

```
POST /chat/query-with-data
Content-Type: application/json

{
  "message": "Show players with high performance and low injury risk",
  "role": "coach"
}
```

Response:
```json
{
  "response": "I found 8 players who are both high performers and low injury risk...",
  "query_type": "advanced",
  "sql_generated": "SELECT * FROM athlete_predictions WHERE...",
  "data": [
    {"player_name": "De Bruyne", "performance_score": 88.5, ...},
    ...
  ],
  "timestamp": "2024-01-15T10:40:00Z"
}
```

### Player Data

```
GET /player/{player_id}/stats
GET /player/{player_id}/injury-details
```

### Team Data

```
GET /team/overview
```

### Insights

```
POST /insights/generate
Content-Type: application/json

{
  "player_id": 123,
  "analysis_type": "injury_prevention"
}
```

## 🧠 Groq Integration Details

### API Key

The Groq API key is configured in `streamlit_app/backend/api.py`:

```python
groq_client = Groq(api_key="your_groq_api_key_here")
```

To use a different key, either:

1. Update the .env file and modify api.py to read from it
2. Set environment variable: `GROQ_API_KEY=your_key`

### Model

The backend uses: **mixtral-8x7b-32768**

To change the model, edit `streamlit_app/backend/api.py`:

```python
response = groq_client.chat.completions.create(
    model="mixtral-8x7b-32768",  # Change this
    messages=[...],
)
```

Available models:
- `mixtral-8x7b-32768` (fast, good for analytics)
- `llama2-70b-4096` (more powerful)
- `gemma-7b-it` (smaller, faster)

## 🔍 Troubleshooting

### "Backend unavailable" Error

**Issue**: Streamlit shows "Backend unavailable. Ensure FastAPI is running at http://localhost:8000"

**Solution**:
1. Check FastAPI is running: `curl http://localhost:8000/health`
2. Verify port 8000 is not in use: `netstat -ano | findstr :8000` (Windows)
3. Restart backend: `python -m uvicorn streamlit_app.backend.api:app --port 8000`

### Snowflake Connection Failed

**Issue**: "snowflake.connector.errors.OperationalError: 401: Authentication failed"

**Solution**:
1. Verify credentials in .env and api.py
2. Check Snowflake account is active
3. Reset password if needed
4. Test with: `python -c "import snowflake.connector; ..."`

### Groq API Errors

**Issue**: "RateLimitError" or "AuthenticationError from Groq"

**Solution**:
1. Check API key in .env is correct
2. Verify Groq plan allows API requests
3. Check rate limits: https://console.groq.com/
4. Try simpler queries first

### Port Already in Use

**Issue**: "Address already in use" on port 8000 or 8501

**Solution**:
```bash
# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
Stop-Process -Id <PID> -Force

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

Or use different ports:
```bash
python -m uvicorn streamlit_app.backend.api:app --port 8001
streamlit run streamlit_app/app.py --server.port=8502
```

## 📊 Database Schema

Expected tables in `sports_db.analytics`:

```sql
-- Player predictions (created by pipeline)
athlete_predictions (
  player_id INT,
  player_name VARCHAR,
  team_long_name VARCHAR,
  performance_score FLOAT,
  injury_risk_label VARCHAR,
  injury_risk_prob FLOAT,
  recommendation TEXT,
  predicted_at TIMESTAMP
)

-- Player attributes
player_stats (
  player_id INT,
  player_name VARCHAR,
  skill_dribble FLOAT,
  skill_curve FLOAT,
  ... (other skill attributes)
)

-- Injury data
player_injury (
  player_id INT,
  fatigue_index FLOAT,
  training_load FLOAT,
  minutes_played INT,
  matches_last_7_days INT,
  recovery_time FLOAT,
  previous_injury BOOLEAN
)
```

## 🚢 Deployment

### Local Development

The scripts above are optimized for local development with hot-reload enabled.

### Production Deployment

For production:

1. **Disable Hot-Reload**:
   ```bash
   python -m uvicorn streamlit_app.backend.api:app --host 0.0.0.0 --port 8000
   ```

2. **Use Environment Variables** for credentials instead of hardcoding

3. **Deploy on Cloud** (AWS, Azure, Google Cloud):
   - Deploy FastAPI on cloud VM or serverless (e.g., AWS Lambda)
   - Deploy Streamlit on Streamlit Cloud or Docker
   - Use Snowflake-connected warehouse

4. **Docker Example**:
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY streamlit_app ./
   RUN pip install -r backend/requirements.txt streamlit
   EXPOSE 8000 8501
   CMD ["sh", "-c", "python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 & streamlit run app.py"]
   ```

## 📚 Further Reading

- [Streamlit Docs](https://docs.streamlit.io/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Groq API Docs](https://console.groq.com/docs)
- [Snowflake Python Connector](https://github.com/snowflakedb/snowflake-connector-python)

## 📞 Support

For issues or questions:

1. Check the Troubleshooting section above
2. Review API logs in terminal
3. Check FastAPI docs at http://localhost:8000/docs
4. Verify Snowflake connection with provided test script

---

**Last Updated**: January 2024  
**Version**: 1.0.0
