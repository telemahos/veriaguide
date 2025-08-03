#!/bin/bash

# VeriaGuide Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default values
ENVIRONMENT="development"
COMPOSE_FILE="docker-compose.yml"
BUILD_FLAG=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Set environment (development, staging, production)"
            echo "  --build                  Force rebuild of containers"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "Deploying VeriaGuide in $ENVIRONMENT environment..."

# Set compose file based on environment
case $ENVIRONMENT in
    production)
        COMPOSE_FILE="docker-compose.production.yml"
        ;;
    staging)
        COMPOSE_FILE="docker-compose.staging.yml"
        if [ ! -f "$COMPOSE_FILE" ]; then
            print_warning "Staging compose file not found, using production config"
            COMPOSE_FILE="docker-compose.production.yml"
        fi
        ;;
    development)
        COMPOSE_FILE="docker-compose.yml"
        ;;
    *)
        print_error "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "Compose file $COMPOSE_FILE not found!"
    exit 1
fi

# Check if .env file exists for production/staging
if [ "$ENVIRONMENT" != "development" ] && [ ! -f ".env" ]; then
    print_warning ".env file not found. Please create one based on .env.example"
    if [ -f ".env.example" ]; then
        print_status "Example .env file available at .env.example"
    fi
fi

# Pre-deployment checks
print_status "Running pre-deployment checks..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed or not in PATH"
    exit 1
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down

# Pull latest images (for production)
if [ "$ENVIRONMENT" = "production" ]; then
    print_status "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull
fi

# Build and start containers
print_status "Starting containers..."
docker-compose -f "$COMPOSE_FILE" up -d $BUILD_FLAG

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Health checks
print_status "Running health checks..."

# Check if containers are running
CONTAINERS=$(docker-compose -f "$COMPOSE_FILE" ps -q)
for container in $CONTAINERS; do
    if [ "$(docker inspect -f '{{.State.Running}}' $container)" != "true" ]; then
        print_error "Container $container is not running"
        docker-compose -f "$COMPOSE_FILE" logs $container
        exit 1
    fi
done

# Check application health endpoint
if command -v curl &> /dev/null; then
    FRONTEND_PORT=$(grep -E "^\s*-\s*\".*:8000\"" "$COMPOSE_FILE" | sed 's/.*"\(.*\):8000".*/\1/' || echo "8000")
    
    print_status "Checking application health on port $FRONTEND_PORT..."
    
    for i in {1..30}; do
        if curl -f -s "http://localhost:$FRONTEND_PORT/health" > /dev/null; then
            print_status "✅ Application is healthy!"
            break
        fi
        
        if [ $i -eq 30 ]; then
            print_error "❌ Application health check failed after 30 attempts"
            docker-compose -f "$COMPOSE_FILE" logs frontend
            exit 1
        fi
        
        print_status "Waiting for application to be ready... (attempt $i/30)"
        sleep 2
    done
else
    print_warning "curl not available, skipping health check"
fi

# Show running containers
print_status "Deployment completed! Running containers:"
docker-compose -f "$COMPOSE_FILE" ps

# Show useful URLs
case $ENVIRONMENT in
    development)
        print_status "🌐 Application: http://localhost:8000"
        print_status "📊 WordPress Admin: http://localhost:8086/wp-admin"
        print_status "🔧 Cache Info: http://localhost:8000/admin/cache-info"
        ;;
    *)
        print_status "🌐 Application: http://localhost:$FRONTEND_PORT"
        print_status "🔧 Health Check: http://localhost:$FRONTEND_PORT/health"
        ;;
esac

print_status "Deployment completed successfully! 🚀"