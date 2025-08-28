#!/bin/bash

echo "🚀 Starting VeriaGuide in DEVELOPMENT mode..."
echo "📍 Frontend: http://localhost:8000"
echo "📍 WordPress: http://localhost:8086"
echo "📍 Redis: localhost:6379"
echo "📍 Database: localhost:3306"
echo ""

# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

echo "✅ Development environment started!"