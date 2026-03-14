@echo off
REM Football Analytics Platform - Docker Helper Script for Windows

setlocal enabledelayedexpansion

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  Football Analytics Platform - Docker Helper                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

if "%1"=="" goto usage
if "%1"=="help" goto usage
if "%1"=="build" goto build
if "%1"=="up" goto up
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="shell" goto shell
if "%1"=="ps" goto ps_status
if "%1"=="down" goto down
if "%1"=="clean" goto clean
if "%1"=="env-setup" goto env_setup
if "%1"=="status" goto status
if "%1"=="test" goto test
goto unknown

:usage
echo Usage: docker-help.bat [command]
echo.
echo Commands:
echo   build           Build Docker image
echo   up              Start services in foreground
echo   start           Start services in background
echo   stop            Stop all services
echo   restart         Restart all services
echo   logs            View service logs
echo   shell           Access container shell
echo   ps              Show running containers
echo   down            Stop and remove containers
echo   clean           Remove images and containers
echo   env-setup       Create .env file from example
echo   status          Check container status
echo   test            Test backend connectivity
echo   help            Show this help message
echo.
goto end

:build
echo [*] Building Docker image...
docker-compose build
echo.
set "msg=Build complete"
goto success

:up
echo [*] Starting services in foreground...
docker-compose up
goto end

:start
echo [*] Starting services in background...
docker-compose up -d
timeout /t 3 /nobreak
echo [+] Services started
goto ps_status_skip

:stop
echo [*] Stopping services...
docker-compose stop
set "msg=Services stopped"
goto success

:restart
echo [*] Restarting services...
docker-compose restart
set "msg=Services restarted"
goto success

:logs
docker-compose logs -f
goto end

:shell
echo [*] Accessing container shell...
docker-compose exec football-app bash
goto end

:ps_status
echo [*] Container Status:
docker-compose ps
echo.
echo Service URLs:
echo   Streamlit: http://localhost:8501
echo   FastAPI:   http://localhost:8000/docs
echo.
goto end

:ps_status_skip
goto end

:down
echo [*] Stopping and removing containers...
docker-compose down
set "msg=Containers removed"
goto success

:clean
echo [!] This will remove all Football Analytics containers and images
set /p confirm="Continue? (y/N): "
if /i "!confirm!"=="y" (
    docker-compose down -v
    docker rmi football-analytics-platform:latest 2>nul
    set "msg=Cleanup complete"
    goto success
) else (
    echo Cleanup cancelled
    goto end
)

:env_setup
if exist ".env" (
    echo [!] .env file already exists
    set /p overwrite="Overwrite? (y/N): "
    if not /i "!overwrite!"=="y" goto end
)
copy .env.example .env >nul
echo [+] Created .env file
echo [!] Please edit .env with your credentials:
echo   - SNOWFLAKE_PASSWORD
echo   - GROQ_API_KEY
echo.
set /p editnow="Open .env in editor? (y/N): "
if /i "!editnow!"=="y" (
    start notepad .env
)
goto end

:status
echo [*] Checking Football Analytics Platform Status...
echo.
docker-compose ps | findstr "running" >nul
if errorlevel 1 (
    echo [-] Services are not running
    echo    Start services with: docker-help.bat start
) else (
    echo [+] Services are running
    call :ps_status
)
goto end

:test
echo [*] Testing backend connectivity...
echo.
docker-compose ps | findstr "running" >nul
if errorlevel 1 (
    echo [-] Services are not running
    echo    Start them with: docker-help.bat start
    goto end
)

echo [*] Testing Streamlit...
powershell -Command "try { $response = Invoke-WebRequest http://localhost:8501 -UseBasicParsing; Write-Host '[+] Streamlit is responding' } catch { Write-Host '[-] Streamlit is not responding' }"

echo [*] Testing FastAPI...
powershell -Command "try { $response = Invoke-WebRequest http://localhost:8000/docs -UseBasicParsing; Write-Host '[+] FastAPI is responding' } catch { Write-Host '[-] FastAPI is not responding' }"

echo.
echo [+] Service URLs:
echo    Streamlit: http://localhost:8501
echo    FastAPI:   http://localhost:8000/docs
goto end

:success
echo [+] %msg%
goto end

:unknown
echo [-] Unknown command: %1
echo Run 'docker-help.bat help' for usage information
goto end

:end
endlocal
