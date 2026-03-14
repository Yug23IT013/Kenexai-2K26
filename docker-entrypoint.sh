#!/bin/bash

# Football Analytics Platform - Docker Entrypoint
# Starts both FastAPI backend and Streamlit frontend

set -e

echo "🚀 Starting Football Analytics Platform..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verify environment variables
if [ -z "$SNOWFLAKE_PASSWORD" ]; then
    echo "⚠️  Warning: SNOWFLAKE_PASSWORD not set"
fi

if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  Warning: GROQ_API_KEY not set"
fi

# Start FastAPI backend in background
echo "📡 Starting FastAPI backend on port 8000..."
cd /app/streamlit_app/backend
python -m uvicorn api:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start. Logs:"
    cat /tmp/backend.log
    exit 1
fi

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend on port 8501..."
cd /app/streamlit_app

# Configure streamlit
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml << 'EOF'
[browser]
gatherUsageStats = false

[server]
headless = true
enableXsrfProtection = false
enableCORS = false

[logger]
level = "warning"
EOF

# Run Streamlit app
python -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0

# Keep container running
wait $BACKEND_PID
