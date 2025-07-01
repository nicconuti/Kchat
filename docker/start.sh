#!/bin/bash

# Kchat Docker Startup Script
# This script helps start the Kchat application with Docker Compose

set -e

echo "🚀 Starting Kchat Application"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  prod      Start production environment"
    echo "  dev       Start development environment"
    echo "  test      Run tests in container"
    echo "  stop      Stop all services"
    echo "  logs      Show logs from all services"
    echo "  clean     Clean up containers and volumes"
    echo "  help      Show this help message"
    echo ""
}

# Function to wait for service to be healthy
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep "$service_name" | grep -q "healthy"; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to become healthy after $max_attempts attempts"
    return 1
}

# Function to start production environment
start_production() {
    echo "🏭 Starting production environment..."
    
    # Pull latest images
    docker-compose pull
    
    # Start services
    docker-compose up -d qdrant ollama
    
    # Wait for dependencies
    wait_for_service "kchat-qdrant" || exit 1
    wait_for_service "kchat-ollama" || exit 1
    
    # Download required models
    echo "📥 Downloading required LLM models..."
    docker-compose exec ollama ollama pull mistral
    docker-compose exec ollama ollama pull deepseek-r1:14b
    docker-compose exec ollama ollama pull openchat
    
    # Start main application
    docker-compose up -d kchat
    
    echo "✅ Production environment started!"
    echo "🌐 Kchat is available at: http://localhost:8000"
    echo "📊 Qdrant dashboard: http://localhost:6333/dashboard"
    echo "🤖 Ollama API: http://localhost:11434"
}

# Function to start development environment
start_development() {
    echo "🛠️ Starting development environment..."
    
    # Start with dev profile
    docker-compose --profile dev up -d qdrant ollama
    
    # Wait for dependencies
    wait_for_service "kchat-qdrant" || exit 1
    wait_for_service "kchat-ollama" || exit 1
    
    # Download required models
    echo "📥 Downloading required LLM models..."
    docker-compose exec ollama ollama pull mistral
    docker-compose exec ollama ollama pull deepseek-r1:14b
    docker-compose exec ollama ollama pull openchat
    
    # Start dev application
    docker-compose --profile dev up -d kchat-dev
    
    echo "✅ Development environment started!"
    echo "🌐 Kchat dev is available at: http://localhost:8001"
    echo "📁 Code is mounted for live editing"
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests in container..."
    
    docker-compose --profile test build kchat-test
    docker-compose --profile test run --rm kchat-test
    
    echo "✅ Tests completed!"
}

# Function to show logs
show_logs() {
    echo "📋 Showing logs from all services..."
    docker-compose logs -f
}

# Function to stop services
stop_services() {
    echo "🛑 Stopping all services..."
    docker-compose --profile dev --profile test down
    echo "✅ All services stopped!"
}

# Function to clean up
cleanup() {
    echo "🧹 Cleaning up containers and volumes..."
    read -p "This will remove all containers and volumes. Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose --profile dev --profile test down -v --remove-orphans
        docker system prune -f
        echo "✅ Cleanup completed!"
    else
        echo "❌ Cleanup cancelled."
    fi
}

# Main script logic
case "${1:-help}" in
    "prod")
        start_production
        ;;
    "dev")
        start_development
        ;;
    "test")
        run_tests
        ;;
    "stop")
        stop_services
        ;;
    "logs")
        show_logs
        ;;
    "clean")
        cleanup
        ;;
    "help"|*)
        show_usage
        ;;
esac