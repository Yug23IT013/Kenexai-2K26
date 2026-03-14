#!/bin/bash

# run_app.sh
# Startup script for running both FastAPI backend and Streamlit frontend on macOS/Linux

echo "🚀 Football Analytics Platform Startup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Install backend dependencies
echo ""
echo "📦 Installing backend dependencies..."
pip3 install -q -r streamlit_app/backend/requirements.txt
if [ $? -ne 0 ]; then
    echo "⚠️  Some backend dependencies may have failed to install"
fi

# Check for .env file in backend
ENV_FILE="streamlit_app/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "⚠️  No .env file found in streamlit_app/backend/"
    echo "   Creating .env with sample configuration..."
    cat > "$ENV_FILE" << 'EOF'
# Backend environment configuration

# Snowflake (optional - defaults are in api.py)
SNOWFLAKE_ACCOUNT=your_snowflake_account_here
SNOWFLAKE_USER=MARK
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=sports_db
SNOWFLAKE_SCHEMA=analytics
SNOWFLAKE_WAREHOUSE=SPORTS_WH

# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# Backend Configuration
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
EOF
    echo "   ✓ Created $ENV_FILE"
    echo "   ⚠️  UPDATE PASSWORD in .env before running!"
fi

echo ""
echo "🚀 Starting services..."
echo ""
echo "1. FastAPI Backend"
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "2. Streamlit Frontend"
echo "   URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop services"
echo ""

# Start backend in background
echo "[Backend] Starting FastAPI on port 8000..."
python3 -m uvicorn streamlit_app.backend.api:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend in background
echo "[Frontend] Starting Streamlit on port 8501..."
streamlit run streamlit_app/app.py --server.port=8501 --server.address=localhost &
FRONTEND_PID=$!

echo "✓ FastAPI Backend PID: $BACKEND_PID"
echo "✓ Streamlit Frontend PID: $FRONTEND_PID"

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Services stopped'; exit" SIGINT SIGTERM

# Wait for both processes
wait
