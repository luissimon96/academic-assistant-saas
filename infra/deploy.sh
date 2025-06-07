#!/bin/bash

# Academic Assistant SaaS - Deploy Script
# Deploy to Vercel (Frontend) + Render (Backend)

set -e

echo "🚀 Academic Assistant SaaS - Deploy Pipeline"
echo "============================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}📁 Project root: ${PROJECT_ROOT}${NC}"

# Check if we're in the right directory
if [ ! -d "${PROJECT_ROOT}/frontend" ] || [ ! -d "${PROJECT_ROOT}/backend" ]; then
    echo -e "${RED}❌ Error: Invalid project structure${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo -e "${BLUE}🔧 Checking dependencies...${NC}"

if ! command_exists vercel; then
    echo -e "${YELLOW}⚠️  Vercel CLI not found. Installing...${NC}"
    npm install -g vercel
fi

if ! command_exists git; then
    echo -e "${RED}❌ Git not found. Please install Git.${NC}"
    exit 1
fi

# Environment check
echo -e "${BLUE}🔍 Checking environment configuration...${NC}"

# Check backend .env
if [ ! -f "${PROJECT_ROOT}/backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Backend .env not found. Creating from example...${NC}"
    cp "${PROJECT_ROOT}/backend/env.example" "${PROJECT_ROOT}/backend/.env"
    echo -e "${RED}❌ Please configure ${PROJECT_ROOT}/backend/.env with your actual values${NC}"
    exit 1
fi

# Check frontend .env.local
if [ ! -f "${PROJECT_ROOT}/frontend/.env.local" ]; then
    echo -e "${YELLOW}⚠️  Frontend .env.local not found.${NC}"
    echo -e "${RED}❌ Please create ${PROJECT_ROOT}/frontend/.env.local with:${NC}"
    echo "NEXT_PUBLIC_SUPABASE_URL=your-supabase-url"
    echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key"
    echo "NEXT_PUBLIC_API_URL=your-backend-url"
    exit 1
fi

# Build and test
echo -e "${BLUE}🏗️  Building applications...${NC}"

# Test backend
echo -e "${YELLOW}Testing backend...${NC}"
cd "${PROJECT_ROOT}/backend"
if [ ! -d "venv" ]; then
    python -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
python -c "import main; print('✅ Backend imports OK')"

# Test frontend
echo -e "${YELLOW}Testing frontend...${NC}"
cd "${PROJECT_ROOT}/frontend"
npm install
npm run build
echo -e "${GREEN}✅ Frontend build successful${NC}"

# Deploy Backend to Render
echo -e "${BLUE}🚀 Deploying backend to Render...${NC}"
cd "${PROJECT_ROOT}"

# Check if git repo is clean
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Uncommitted changes found. Committing...${NC}"
    git add .
    git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# Push to main branch
git push origin main

echo -e "${GREEN}✅ Backend deployed to Render${NC}"
echo -e "${BLUE}🔗 Backend will be available at: https://your-app-name.onrender.com${NC}"

# Deploy Frontend to Vercel
echo -e "${BLUE}🚀 Deploying frontend to Vercel...${NC}"
cd "${PROJECT_ROOT}/frontend"

# Deploy to Vercel
vercel --prod

echo -e "${GREEN}✅ Frontend deployed to Vercel${NC}"

# Success message
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo -e "${GREEN}✅ Frontend: Deployed to Vercel${NC}"
echo -e "${GREEN}✅ Backend: Deployed to Render${NC}"
echo ""
echo -e "${YELLOW}🔗 Next steps:${NC}"
echo "1. Update frontend .env.local with actual backend URL"
echo "2. Configure custom domain (optional)"
echo "3. Set up monitoring and alerts"
echo "4. Test all functionality in production"
echo ""
echo -e "${BLUE}💡 Monitor your deployments:${NC}"
echo "- Vercel Dashboard: https://vercel.com/dashboard"
echo "- Render Dashboard: https://dashboard.render.com"
echo ""
echo -e "${GREEN}🚀 Your Academic Assistant SaaS is now live!${NC}" 