#!/bin/bash

# Development startup script for CRE PDF Extractor Web App

set -e

echo "🚀 Starting CRE PDF Extractor Web Application"
echo "================================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp backend/.env.example .env
    echo "✅ Created .env file. Please edit it with your API keys before continuing."
    echo "   Required keys: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY"
    exit 1
fi

# Check if frontend .env.local exists
if [ ! -f "frontend/.env.local" ]; then
    echo "📝 Creating frontend .env.local..."
    cp frontend/.env.local.example frontend/.env.local
fi

# Check for Docker
if command -v docker &> /dev/null; then
    echo "🐳 Docker detected. Starting with Docker Compose..."

    # Try new docker compose command first, fall back to docker-compose
    if docker compose version &> /dev/null; then
        docker compose up --build
    elif command -v docker-compose &> /dev/null; then
        docker-compose up --build
    else
        echo "⚠️  Docker found but Docker Compose is not available."
        echo "Please install Docker Compose or run services manually."
        exit 1
    fi
else
    echo "⚠️  Docker not found. Please install Docker and Docker Compose, or run services manually."
    echo ""
    echo "Manual startup instructions:"
    echo "1. Backend:"
    echo "   cd backend && pip install -r requirements.txt"
    echo "   python app.py"
    echo ""
    echo "2. Frontend (in new terminal):"
    echo "   cd frontend && npm install"
    echo "   npm run dev"
    exit 1
fi
