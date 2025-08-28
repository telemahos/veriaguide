#!/bin/bash

# VeriaGuide Production Startup
# This script starts all production services from a single Docker Compose file.
# It assumes a host-level web server (OpenLiteSpeed) is proxying to Traefik.
# Usage: ./start-production-docker.sh

set -e

echo "🚀 Starting VeriaGuide Production Stack..."

# Define the single Compose file
COMPOSE_FILE="docker-compose.prod.yml"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: $COMPOSE_FILE not found!"
    exit 1
fi

# Check if production environment file exists
if [ ! -f ".env.production.docker" ]; then
    echo "❌ Error: .env.production.docker file not found!"
    exit 1
fi

# Stop any existing containers defined in the compose file
echo "🛑 Stopping existing containers..."
docker compose -f $COMPOSE_FILE down --remove-orphans 2>/dev/null || true

# Start production stack
echo "🌟 Starting all containers with Traefik Proxy on custom ports..."
docker compose -f $COMPOSE_FILE --env-file .env.production.docker up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Check service status
echo "📊 Service Status:"
docker compose -f $COMPOSE_FILE ps

echo ""
echo "🎉 VeriaGuide Production Stack started!"

echo ""
echo "📋 Access URL:"
echo "   Main Site: https://veriaguide.gr"
echo "   Traefik Dashboard: http://localhost:8080 (if accessing from the server itself)"

echo ""
echo "IMPORTANT: Configure your OpenLiteSpeed server to act as a reverse proxy."
echo "Proxy all traffic for https://veriaguide.gr to https://127.0.0.1:8443"

echo ""
echo "📝 To view logs:"
echo "   docker compose -f $COMPOSE_FILE logs -f"
echo ""
echo "🛑 To stop:"
echo "   docker compose -f $COMPOSE_FILE down"
