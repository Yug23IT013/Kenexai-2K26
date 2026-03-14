# run_app.ps1
# Startup script for running both FastAPI backend and Streamlit frontend

Write-Host "🚀 Football Analytics Platform Startup" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Python found: $(python --version)" -ForegroundColor Green

# Install backend dependencies
Write-Host ""
Write-Host "📦 Installing backend dependencies..." -ForegroundColor Yellow
pip install -q -r streamlit_app/backend/requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Some backend dependencies may have failed to install" -ForegroundColor Yellow
}

# Check for .env file in backend
$envFile = "streamlit_app/backend/.env"
if (-not (Test-Path $envFile)) {
    Write-Host ""
    Write-Host "⚠️  No .env file found in streamlit_app/backend/" -ForegroundColor Yellow
    Write-Host "   Creating .env with sample configuration..." -ForegroundColor Yellow
    @"
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
"@ | Out-File -Encoding UTF8 $envFile
    Write-Host "   ✓ Created $envFile" -ForegroundColor Green
    Write-Host "   ⚠️  UPDATE PASSWORD in .env before running!" -ForegroundColor Red
}

Write-Host ""
Write-Host "🚀 Starting services..." -ForegroundColor Green
Write-Host ""
Write-Host "1. FastAPI Backend" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:8000" -ForegroundColor Gray
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Streamlit Frontend" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:8501" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop services" -ForegroundColor Yellow
Write-Host ""

# Create two background jobs to run both services
$backend = Start-Job -ScriptBlock {
    Set-Location (Split-Path $using:PSScriptRoot)
    Write-Host "[Backend]" -ForegroundColor Cyan -NoNewline
    Write-Host " Starting FastAPI on port 8000..." -ForegroundColor Gray
    python -m uvicorn streamlit_app.backend.api:app --host 0.0.0.0 --port 8000 --reload
}

$frontend = Start-Job -ScriptBlock {
    Set-Location (Split-Path $using:PSScriptRoot)
    Write-Host "[Frontend]" -ForegroundColor Cyan -NoNewline
    Write-Host " Starting Streamlit on port 8501..." -ForegroundColor Gray
    streamlit run streamlit_app/app.py --server.port=8501 --server.address=localhost
}

Write-Host "✓ FastAPI Backend job: $($backend.Id)" -ForegroundColor Green
Write-Host "✓ Streamlit Frontend job: $($frontend.Id)" -ForegroundColor Green

# Wait for both jobs
Wait-Job -Job $backend, $frontend

# Handle cleanup on exit
if ($error) {
    Write-Host "❌ Error occurred" -ForegroundColor Red
    Write-Host $error
}

Write-Host ""
Write-Host "Stopping services..." -ForegroundColor Yellow
Stop-Job -Job $backend, $frontend -Force
Remove-Job -Job $backend, $frontend -Force

Write-Host "✓ Services stopped" -ForegroundColor Green
Write-Host "Goodbye! 👋" -ForegroundColor Green
