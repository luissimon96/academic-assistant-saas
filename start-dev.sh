#!/bin/bash

# Academic Assistant SaaS - Development Startup Script

echo "🚀 Starting Academic Assistant SaaS Development Environment"
echo "=================================================="

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the academic-assistant-saas directory"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Installing dependencies...${NC}"

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "✅ Frontend dependencies already installed"
fi

# Install backend dependencies  
echo -e "${YELLOW}Installing backend dependencies...${NC}"
cd ../backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Backend virtual environment already exists"
    source venv/bin/activate
    pip install -r requirements.txt --quiet
fi

cd ..

echo -e "${GREEN}✅ Dependencies installed successfully!${NC}"
echo ""

# Check for environment files
echo -e "${BLUE}🔧 Checking environment configuration...${NC}"

if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Backend .env file not found. Please create one based on backend/env.example${NC}"
    echo "   cp backend/env.example backend/.env"
fi

if [ ! -f "frontend/.env.local" ]; then
    echo -e "${YELLOW}⚠️  Frontend .env.local file not found. Please create one for Supabase config${NC}"
    echo "   Create frontend/.env.local with:"
    echo "   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url"
    echo "   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key"
fi

echo ""
echo -e "${GREEN}🎯 Ready to start development servers!${NC}"
echo ""
echo "To start the services:"
echo -e "${BLUE}Frontend (Next.js):${NC} cd frontend && npm run dev"
echo -e "${BLUE}Backend (FastAPI):${NC}  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo ""
echo "Access points:"
echo -e "${GREEN}🌐 Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}🔧 Backend API:${NC} http://localhost:8000"
echo -e "${GREEN}📚 API Docs:${NC} http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}💡 Tip: Open two terminals to run both services simultaneously${NC}"
echo "==================================================" 