#!/bin/bash
# Football Analytics Platform - Docker Helper Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Display banner
banner() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Football Analytics Platform - Docker Helper                 ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Display usage
usage() {
    banner
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build           Build Docker image"
    echo "  up              Start services in foreground"
    echo "  start           Start services in background"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  logs            View service logs"
    echo "  logs-backend    View backend logs"
    echo "  shell           Access container shell"
    echo "  ps              Show running containers"
    echo "  down            Stop and remove containers"
    echo "  clean           Remove images and containers"
    echo "  env-setup       Create .env file from example"
    echo "  status          Check container status"
    echo "  test            Test backend connectivity"
    echo "  help            Show this help message"
    echo ""
}

# Build image
build() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker-compose build
    echo -e "${GREEN}✓ Build complete${NC}"
}

# Start services in foreground
up() {
    echo -e "${YELLOW}Starting services in foreground...${NC}"
    docker-compose up
}

# Start services in background
start() {
    echo -e "${YELLOW}Starting services in background...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✓ Services started${NC}"
    sleep 3
    ps
}

# Stop services
stop() {
    echo -e "${YELLOW}Stopping services...${NC}"
    docker-compose stop
    echo -e "${GREEN}✓ Services stopped${NC}"
}

# Restart services
restart() {
    echo -e "${YELLOW}Restarting services...${NC}"
    docker-compose restart
    echo -e "${GREEN}✓ Services restarted${NC}"
}

# View logs
logs() {
    docker-compose logs -f
}

# View backend logs
logs_backend() {
    echo -e "${YELLOW}Backend logs:${NC}"
    docker-compose logs -f football-app | grep backend
}

# Access container shell
shell() {
    echo -e "${YELLOW}Accessing container shell...${NC}"
    docker-compose exec football-app bash
}

# Show container status
ps_status() {
    echo -e "${YELLOW}Container Status:${NC}"
    docker-compose ps
    echo ""
    echo -e "${BLUE}Service URLs:${NC}"
    echo -e "  ${GREEN}Streamlit${NC}:  http://localhost:8501"
    echo -e "  ${GREEN}FastAPI${NC}:    http://localhost:8000/docs"
}

# Stop and remove containers
down() {
    echo -e "${YELLOW}Stopping and removing containers...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ Containers removed${NC}"
}

# Clean up images and containers
clean() {
    echo -e "${RED}Cleaning up Docker resources...${NC}"
    read -p "This will remove all Football Analytics containers and images. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker rmi football-analytics-platform:latest 2>/dev/null || true
        echo -e "${GREEN}✓ Cleanup complete${NC}"
    else
        echo "Cleanup cancelled"
    fi
}

# Setup .env file
env_setup() {
    if [ -f ".env" ]; then
        echo -e "${YELLOW}.env file already exists${NC}"
        read -p "Overwrite? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}Please edit .env with your credentials:${NC}"
    echo "  - SNOWFLAKE_PASSWORD"
    echo "  - GROQ_API_KEY"
    echo ""
    read -p "Open .env in editor? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v code &> /dev/null; then
            code .env
        elif command -v nano &> /dev/null; then
            nano .env
        else
            echo "Please edit .env manually"
        fi
    fi
}

# Check service status
status() {
    echo -e "${BLUE}Checking Football Analytics Platform Status...${NC}"
    echo ""
    
    if docker-compose ps | grep -q "running"; then
        echo -e "${GREEN}✓ Services are running${NC}"
        ps_status
    else
        echo -e "${RED}✗ Services are not running${NC}"
        echo "Start services with: $0 start"
    fi
}

# Test backend connectivity
test_connectivity() {
    echo -e "${YELLOW}Testing backend connectivity...${NC}"
    
    if docker-compose ps | grep -q "running"; then
        echo ""
        echo -e "${BLUE}Testing Streamlit...${NC}"
        if curl -s http://localhost:8501 > /dev/null; then
            echo -e "${GREEN}✓ Streamlit is responding${NC}"
        else
            echo -e "${RED}✗ Streamlit is not responding${NC}"
        fi
        
        echo -e "${BLUE}Testing FastAPI...${NC}"
        if curl -s http://localhost:8000/docs > /dev/null; then
            echo -e "${GREEN}✓ FastAPI is responding${NC}"
        else
            echo -e "${RED}✗ FastAPI is not responding${NC}"
        fi
        
        echo ""
        echo -e "${GREEN}Service URLs:${NC}"
        echo "  Streamlit:  http://localhost:8501"
        echo "  FastAPI:    http://localhost:8000/docs"
    else
        echo -e "${RED}Services are not running${NC}"
        echo "Start them with: $0 start"
    fi
}

# Main script
if [ $# -eq 0 ]; then
    usage
    exit 0
fi

case "$1" in
    build)
        build
        ;;
    up)
        up
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    logs-backend)
        logs_backend
        ;;
    shell)
        shell
        ;;
    ps)
        ps_status
        ;;
    down)
        down
        ;;
    clean)
        clean
        ;;
    env-setup)
        env_setup
        ;;
    status)
        status
        ;;
    test)
        test_connectivity
        ;;
    help)
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

exit $?
