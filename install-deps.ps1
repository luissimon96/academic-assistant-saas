# 🚀 Academic Assistant SaaS - Dependency Installation Script (Windows)
# Handles dependency conflicts automatically

Write-Host "🔧 Installing Academic Assistant SaaS Dependencies..." -ForegroundColor Cyan

# Frontend Dependencies
Write-Host "📦 Installing Frontend Dependencies..." -ForegroundColor Yellow
Set-Location frontend

# Try npm ci first, fallback to legacy mode if needed
try {
  npm ci
  Write-Host "✅ Frontend dependencies installed successfully" -ForegroundColor Green
}
catch {
  Write-Host "⚠️  npm ci failed, trying with legacy peer deps..." -ForegroundColor Yellow
  try {
    npm ci --legacy-peer-deps
    Write-Host "✅ Frontend dependencies installed with legacy peer deps" -ForegroundColor Green
  }
  catch {
    Write-Host "❌ Frontend dependency installation failed" -ForegroundColor Red
    exit 1
  }
}

Set-Location ..

# Backend Dependencies
Write-Host "🐍 Installing Backend Dependencies..." -ForegroundColor Yellow
Set-Location backend

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
  Write-Host "🔧 Creating Python virtual environment..." -ForegroundColor Cyan
  python -m venv venv
}

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
pip install --upgrade pip

# Install dependencies with conflict resolution
try {
  pip install -r requirements.txt
  Write-Host "✅ Backend dependencies installed successfully" -ForegroundColor Green
}
catch {
  Write-Host "⚠️  Standard installation failed, trying with dependency resolver..." -ForegroundColor Yellow
  try {
    pip install -r requirements.txt --upgrade-strategy eager
    Write-Host "✅ Backend dependencies installed with eager upgrade" -ForegroundColor Green
  }
  catch {
    Write-Host "❌ Backend dependency installation failed" -ForegroundColor Red
    exit 1
  }
}

Set-Location ..

Write-Host "🎉 All dependencies installed successfully!" -ForegroundColor Green
Write-Host "📚 Next steps:" -ForegroundColor Cyan
Write-Host "1. cd frontend && npm run dev" -ForegroundColor White
Write-Host "2. cd backend && .\venv\Scripts\Activate.ps1 && uvicorn main:app --reload" -ForegroundColor White 