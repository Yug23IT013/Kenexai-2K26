# Football Analytics Platform - Docker Helper for PowerShell
# 
# Usage: 
#   - Open PowerShell in project directory
#   - Run: .\docker-help.ps1 build
#   - Run: .\docker-help.ps1 start
#   
# Note: May need to run "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned" first

param(
    [Parameter(Position = 0)]
    [ValidateSet('build', 'up', 'start', 'stop', 'restart', 'logs', 'shell', 'ps', 'down', 'clean', 'env-setup', 'status', 'test', 'help')]
    [string]$Command = 'help'
)

# Colors for output
$Color = @{
    Red    = 'Red'
    Green  = 'Green'
    Yellow = 'Yellow'
    Blue   = 'Cyan'
}

# Functions
function Show-Banner {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor $Color.Blue
    Write-Host "║  Football Analytics Platform - Docker Helper (PowerShell)    ║" -ForegroundColor $Color.Blue
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor $Color.Blue
    Write-Host ""
}

function Show-Usage {
    Show-Banner
    Write-Host "Usage: docker-help.ps1 [command]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  build           Build Docker image"
    Write-Host "  up              Start services in foreground"
    Write-Host "  start           Start services in background"
    Write-Host "  stop            Stop all services"
    Write-Host "  restart         Restart all services"
    Write-Host "  logs            View service logs"
    Write-Host "  shell           Access container shell"
    Write-Host "  ps              Show running containers"
    Write-Host "  down            Stop and remove containers"
    Write-Host "  clean           Remove images and containers"
    Write-Host "  env-setup       Create .env file from example"
    Write-Host "  status          Check container status"
    Write-Host "  test            Test backend connectivity"
    Write-Host "  help            Show this help message"
    Write-Host ""
}

function Invoke-Build {
    Write-Host "Building Docker image..." -ForegroundColor $Color.Yellow
    docker-compose build
    Write-Host "✓ Build complete" -ForegroundColor $Color.Green
}

function Invoke-Up {
    Write-Host "Starting services in foreground..." -ForegroundColor $Color.Yellow
    docker-compose up
}

function Invoke-Start {
    Write-Host "Starting services in background..." -ForegroundColor $Color.Yellow
    docker-compose up -d
    Write-Host "✓ Services started" -ForegroundColor $Color.Green
    Start-Sleep -Seconds 3
    Invoke-PsStatus
}

function Invoke-Stop {
    Write-Host "Stopping services..." -ForegroundColor $Color.Yellow
    docker-compose stop
    Write-Host "✓ Services stopped" -ForegroundColor $Color.Green
}

function Invoke-Restart {
    Write-Host "Restarting services..." -ForegroundColor $Color.Yellow
    docker-compose restart
    Write-Host "✓ Services restarted" -ForegroundColor $Color.Green
}

function Invoke-Logs {
    docker-compose logs -f
}

function Invoke-Shell {
    Write-Host "Accessing container shell..." -ForegroundColor $Color.Yellow
    docker-compose exec football-app bash
}

function Invoke-PsStatus {
    Write-Host ""
    Write-Host "Container Status:" -ForegroundColor $Color.Yellow
    docker-compose ps
    Write-Host ""
    Write-Host "Service URLs:" -ForegroundColor $Color.Blue
    Write-Host "  Streamlit: http://localhost:8501" -ForegroundColor $Color.Green
    Write-Host "  FastAPI:   http://localhost:8000/docs" -ForegroundColor $Color.Green
    Write-Host ""
}

function Invoke-Down {
    Write-Host "Stopping and removing containers..." -ForegroundColor $Color.Yellow
    docker-compose down
    Write-Host "✓ Containers removed" -ForegroundColor $Color.Green
}

function Invoke-Clean {
    Write-Host "Cleaning up Docker resources..." -ForegroundColor $Color.Red
    $confirm = Read-Host "This will remove all Football Analytics containers and images. Continue? (y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        docker-compose down -v
        docker rmi football-analytics-platform:latest -ErrorAction SilentlyContinue
        Write-Host "✓ Cleanup complete" -ForegroundColor $Color.Green
    }
    else {
        Write-Host "Cleanup cancelled"
    }
}

function Invoke-EnvSetup {
    if (Test-Path ".env") {
        Write-Host ".env file already exists" -ForegroundColor $Color.Yellow
        $overwrite = Read-Host "Overwrite? (y/N)"
        if ($overwrite -ne 'y' -and $overwrite -ne 'Y') {
            return
        }
    }
    
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file" -ForegroundColor $Color.Green
    Write-Host "Please edit .env with your credentials:" -ForegroundColor $Color.Yellow
    Write-Host "  - SNOWFLAKE_PASSWORD"
    Write-Host "  - GROQ_API_KEY"
    Write-Host ""
    
    $editNow = Read-Host "Open .env in editor? (y/N)"
    if ($editNow -eq 'y' -or $editNow -eq 'Y') {
        # Try different editors in order  
        if (Get-Command code -ErrorAction SilentlyContinue) {
            code .env
        }
        elseif (Get-Command notepad -ErrorAction SilentlyContinue) {
            notepad .env
        }
        else {
            Write-Host "Please edit .env manually"
        }
    }
}

function Invoke-Status {
    Write-Host "Checking Football Analytics Platform Status..." -ForegroundColor $Color.Blue
    Write-Host ""
    
    $running = docker-compose ps | Select-String "running"
    if ($running) {
        Write-Host "✓ Services are running" -ForegroundColor $Color.Green
        Invoke-PsStatus
    }
    else {
        Write-Host "✗ Services are not running" -ForegroundColor $Color.Red
        Write-Host "Start services with: docker-help.ps1 start"
    }
}

function Invoke-Test {
    Write-Host "Testing backend connectivity..." -ForegroundColor $Color.Yellow
    Write-Host ""
    
    $running = docker-compose ps | Select-String "running"
    if (-not $running) {
        Write-Host "Services are not running" -ForegroundColor $Color.Red
        Write-Host "Start them with: docker-help.ps1 start"
        return
    }
    
    Write-Host "Testing Streamlit..." -ForegroundColor $Color.Blue
    try {
        $response = Invoke-WebRequest http://localhost:8501 -UseBasicParsing -ErrorAction Stop
        Write-Host "✓ Streamlit is responding" -ForegroundColor $Color.Green
    }
    catch {
        Write-Host "✗ Streamlit is not responding" -ForegroundColor $Color.Red
    }
    
    Write-Host "Testing FastAPI..." -ForegroundColor $Color.Blue
    try {
        $response = Invoke-WebRequest http://localhost:8000/docs -UseBasicParsing -ErrorAction Stop
        Write-Host "✓ FastAPI is responding" -ForegroundColor $Color.Green
    }
    catch {
        Write-Host "✗ FastAPI is not responding" -ForegroundColor $Color.Red
    }
    
    Write-Host ""
    Write-Host "Service URLs:" -ForegroundColor $Color.Green
    Write-Host "  Streamlit: http://localhost:8501"
    Write-Host "  FastAPI:   http://localhost:8000/docs"
}

# Main switch
switch ($Command) {
    'build' { Invoke-Build }
    'up' { Invoke-Up }
    'start' { Invoke-Start }
    'stop' { Invoke-Stop }
    'restart' { Invoke-Restart }
    'logs' { Invoke-Logs }
    'shell' { Invoke-Shell }
    'ps' { Invoke-PsStatus }
    'down' { Invoke-Down }
    'clean' { Invoke-Clean }
    'env-setup' { Invoke-EnvSetup }
    'status' { Invoke-Status }
    'test' { Invoke-Test }
    'help' { Show-Usage }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor $Color.Red
        Write-Host "Run 'docker-help.ps1 help' for usage information"
    }
}
