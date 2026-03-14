# QUICK START GUIDE

## 🚀 Get Started in 5 Minutes

This guide will get your Football Analytics Platform running with Groq AI integration.

### ✅ Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Snowflake credentials (account, user, password)
- [ ] Groq API key (from https://console.groq.com/)
- [ ] Git (optional)

### 📝 Step 1: Configure Environment (2 min)

**1.1 Create configuration file:**

```bash
cd streamlit_app/backend
```

**1.2 Copy example configuration:**

```bash
# On Windows
copy .env.example .env

# On macOS/Linux
cp .env.example .env
```

**1.3 Edit `.env` with your credentials:**

Open `streamlit_app/backend/.env` and replace:

```env
SNOWFLAKE_PASSWORD=your_actual_password_here  # ← Change this!
GROQ_API_KEY=your_groq_api_key_here  # ← Change this!
```

⚠️ **Never commit this file to git!** It already has `.env` in `.gitignore`.

### 🔧 Step 2: Run Setup Script (2 min)

This verifies everything is configured correctly:

```bash
cd ..  # Back to project root
python setup.py
```

The script will:
- ✓ Check Python version
- ✓ Verify pip/streamlit
- ✓ Install all dependencies
- ✓ Test Snowflake connection
- ✓ Test Groq API

**If setup.py reports all ✓**, proceed to Step 3.

**If setup.py reports ❌**, fix the issues it lists.

### 🎬 Step 3: Start the Application (1 min)

**Option A: Automatic (Recommended)**

```bash
# Windows (PowerShell)
.\run_app.ps1

# macOS/Linux
./run_app.sh

# Cross-platform (Python)
python run_app.py
```

**Option B: Manual (Two Terminals)**

Terminal 1:
```bash
python -m uvicorn streamlit_app.backend.api:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2:
```bash
streamlit run streamlit_app/app.py --server.port=8501
```

### 📖 Step 4: Access the App (30 sec)

Wait for output like:

```
[Backend] Starting FastAPI on port 8000...
✓ Uvicorn running on http://0.0.0.0:8000

[Frontend] Starting Streamlit on port 8501...
You can now view your Streamlit app in your browser.
URL: http://localhost:8501
```

Then:

1. Open http://localhost:8501
2. Log in with a test account:
   - Username: `coach_pep`
   - Password: `pass`
3. Go to "Coach Dashboard" → "AI Chatbot" tab
4. Ask a question!

## 🧪 Test the Chatbot

Try these sample questions:

### Coach Dashboard Chatbot

**Question 1: Player Risk**
```
"Show all high-risk players"
```
Expected: List of high-risk players with Groq analysis

**Question 2: Team Performance**
```
"What is the team's overall performance?"
```
Expected: Team statistics from Snowflake + Groq insights

**Question 3: Top Performers**
```
"Who are the top 5 performers this week?"
```
Expected: Player list with performance scores

### Player Dashboard (if logged in as a player)

**Question 1: Personal Score**
```
"What's my current performance score?"
```

**Question 2: Recovery Tips**
```
"What recovery tips do you recommend for me?"
```

## 🔍 Verify Everything is Working

### Check Backend Health

Open in browser or terminal:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### Check FastAPI Documentation

Open: http://localhost:8000/docs

You'll see all available API endpoints with swagger UI.

### Check Streamlit Status

Look for in browser:
- ✓ No red error messages
- ✓ "Chat history" container visible
- ✓ Message input box active

## ❓ Troubleshooting

### "Backend unavailable" Error

**Problem**: Chat shows "❌ Cannot connect to backend at http://localhost:8000"

**Fix**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start it:
python -m uvicorn streamlit_app.backend.api:app --port 8000 --reload
```

### "Snowflake connection failed"

**Problem**: Backend shows "snowflake.connector.errors.OperationalError"

**Fix**:
1. Verify password in `streamlit_app/backend/.env`
2. Test locally:
   ```python
   import snowflake.connector
   conn = snowflake.connector.connect(
       account='your_snowflake_account_here',
       user='MARK',
       password='YOUR_PASSWORD',  # ← Replace
       database='sports_db',
       schema='analytics',
       warehouse='SPORTS_WH'
   )
   print("Connected!")
   ```

### "Groq API error"

**Problem**: Chat says "❌ Error: RateLimitError"

**Fix**:
1. Verify API key in `streamlit_app/backend/.env`
2. Check https://console.groq.com/usage for rate limits
3. Try a simpler question first

### Port Already in Use

**Problem**: "Address already in use: ('0.0.0.0', 8000)"

**Fix**:
```bash
# Kill the existing process
# Windows (PowerShell)
Get-Process -Name python | Stop-Process

# macOS/Linux
killall python
```

Then restart the app.

## 📚 Next Steps

After verifying everything works:

1. **Customize User Accounts**: Edit `streamlit_app/auth.py`
2. **Add More Chat Features**: Edit `streamlit_app/components/chatbot_groq.py`
3. **Modify Snowflake Queries**: Update query logic in `streamlit_app/utils/snowflake_queries.py`
4. **Deploy to Cloud**: See full README.md for deployment instructions

## 📖 Full Documentation

For complete details, see: `streamlit_app/README.md`

---

**Need More Help?**

1. Check the main README.md in the repository
2. Review API documentation at http://localhost:8000/docs
3. Check backend logs in the terminal running FastAPI
4. Review system logs in Streamlit terminal

**Happy analyzing!** 🎉
