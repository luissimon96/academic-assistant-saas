#!/bin/bash

# 🚀 Academic Assistant SaaS - Dependency Installation Script
# Handles dependency conflicts automatically

echo "🔧 Installing Academic Assistant SaaS Dependencies..."

# Frontend Dependencies
echo "📦 Installing Frontend Dependencies..."
cd frontend

# Try npm ci first, fallback to legacy mode if needed
if npm ci; then
    echo "✅ Frontend dependencies installed successfully"
else
    echo "⚠️  npm ci failed, trying with legacy peer deps..."
    if npm ci --legacy-peer-deps; then
        echo "✅ Frontend dependencies installed with legacy peer deps"
    else
        echo "❌ Frontend dependency installation failed"
        exit 1
    fi
fi

cd ..

# Backend Dependencies
echo "🐍 Installing Backend Dependencies..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
pip install --upgrade pip

# Install dependencies with conflict resolution
if pip install -r requirements.txt; then
    echo "✅ Backend dependencies installed successfully"
else
    echo "⚠️  Standard installation failed, trying with dependency resolver..."
    if pip install -r requirements.txt --upgrade-strategy eager; then
        echo "✅ Backend dependencies installed with eager upgrade"
    else
        echo "❌ Backend dependency installation failed"
        exit 1
    fi
fi

cd ..

echo "🎉 All dependencies installed successfully!"
echo "📚 Next steps:"
echo "1. cd frontend && npm run dev"
echo "2. cd backend && source venv/bin/activate && uvicorn main:app --reload" 