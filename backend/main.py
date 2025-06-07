"""
Academic Assistant SaaS - Backend API
FastAPI + Supabase + Multi-LLM Integration
"""

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import uuid
import time
import base64
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
import uvicorn

# Import local modules
from config import settings, PLAN_FEATURES, LLM_ROUTING
from models import (
    ImageUploadRequest, ProcessingResponse, ProcessingResult, RequestStatus,
    UserProfile, UserUsage, RateLimitInfo, HealthCheck, ErrorResponse
)
from services.ocr_service import ocr_service

# Load environment variables
load_dotenv()

# Security
security = HTTPBearer()

# In-memory storage for demo (replace with Redis in production)
user_sessions = {}
processing_requests = {}
usage_tracking = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Academic Assistant API starting...")
    print(f"📊 Environment: {'Development' if settings.debug else 'Production'}")
    print(f"🔗 CORS origins: {settings.cors_origins}")
    yield
    # Shutdown
    print("📝 Academic Assistant API shutting down...")

# Initialize FastAPI
app = FastAPI(
    title="Academic Assistant SaaS API",
    description="API para assistente acadêmico com IA e OCR",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to verify JWT token (mock for now)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """
    Verify JWT token and return current user
    TODO: Implement proper Supabase JWT verification
    """
    token = credentials.credentials
    
    # Mock user for development
    if token in user_sessions:
        return user_sessions[token]
    
    # For demo purposes, create a mock user
    mock_user = UserProfile(
        id=str(uuid.uuid4()),
        email="demo@academicassistant.com.br",
        full_name="Usuário Demo",
        plan="free",
        usage_count=0,
        usage_month=datetime.now().month,
        created_at=datetime.now()
    )
    user_sessions[token] = mock_user
    return mock_user

async def check_rate_limit(user: UserProfile) -> RateLimitInfo:
    """
    Check if user has exceeded their plan limits
    """
    current_month = datetime.now().month
    
    # Reset usage if new month
    if user.usage_month != current_month:
        user.usage_count = 0
        user.usage_month = current_month
        user.usage_reset_date = datetime.now().replace(day=1) + timedelta(days=32)
        user.usage_reset_date = user.usage_reset_date.replace(day=1)
    
    plan_config = PLAN_FEATURES.get(user.plan, PLAN_FEATURES['free'])
    monthly_limit = plan_config['requests_per_month']
    
    # Calculate remaining requests
    if monthly_limit == -1:  # Unlimited
        remaining = 999999
    else:
        remaining = max(0, monthly_limit - user.usage_count)
    
    return RateLimitInfo(
        requests_remaining=remaining,
        reset_time=user.usage_reset_date or datetime.now() + timedelta(days=30),
        plan_limit=monthly_limit,
        current_usage=user.usage_count
    )

# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        version=settings.version,
        timestamp=datetime.now(),
        services={
            "ocr": True,
            "database": True,  # TODO: Check Supabase connection
            "redis": True      # TODO: Check Redis connection
        },
        uptime=time.time()
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Academic Assistant SaaS API",
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
        "status": "operational"
    }

# User profile endpoint
@app.get("/user/profile", response_model=UserProfile)
async def get_user_profile(current_user: UserProfile = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

# User usage endpoint
@app.get("/user/usage", response_model=UserUsage)
async def get_user_usage(current_user: UserProfile = Depends(get_current_user)):
    """Get current user usage statistics"""
    rate_limit = await check_rate_limit(current_user)
    
    return UserUsage(
        user_id=current_user.id,
        current_month_usage=current_user.usage_count,
        plan_limit=rate_limit.plan_limit,
        remaining_requests=rate_limit.requests_remaining,
        reset_date=rate_limit.reset_time,
        plan=current_user.plan
    )

# Main OCR + AI processing endpoint
@app.post("/process", response_model=ProcessingResponse)
async def process_image(
    request: ImageUploadRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Process image with OCR and AI explanation
    """
    # Check rate limits
    rate_limit = await check_rate_limit(current_user)
    if rate_limit.requests_remaining <= 0:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Você excedeu o limite de {rate_limit.plan_limit} solicitações por mês do plano {current_user.plan.upper()}",
                "reset_time": rate_limit.reset_time.isoformat(),
                "upgrade_url": "/plans"
            }
        )
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Step 1: OCR Processing
        print(f"🔍 Processing OCR for request {request_id}")
        ocr_result = ocr_service.extract_text(request.image_data, current_user.plan)
        
        if not ocr_result.success or not ocr_result.text.strip():
            return ProcessingResponse(
                success=False,
                request_id=request_id,
                status=RequestStatus.FAILED,
                error="OCR_FAILED",
                message="Não foi possível extrair texto da imagem. Tente uma imagem mais clara."
            )
        
        # Step 2: AI Processing (mock for now)
        print(f"🤖 Processing AI for request {request_id}")
        
        # Mock AI response based on plan
        plan_config = PLAN_FEATURES.get(current_user.plan, PLAN_FEATURES['free'])
        ai_response = f"""
        **Texto extraído:** {ocr_result.text}
        
        **Análise (Plano {plan_config['name']}):**
        
        Com base no texto extraído, posso ajudar a explicar o conteúdo. 
        
        {"✨ Esta é uma explicação detalhada do plano " + plan_config['name'] + "!" if current_user.plan != 'free' else "💡 Upgrade para o plano Pro para explicações mais detalhadas!"}
        
        **Próximos passos:**
        1. Revise o conteúdo extraído
        2. Faça perguntas específicas se necessário
        3. {"Aproveite as funcionalidades premium!" if current_user.plan != 'free' else "Considere fazer upgrade para mais recursos!"}
        """
        
        # Step 3: Create result
        total_time = time.time() - start_time
        
        result = ProcessingResult(
            request_id=request_id,
            status=RequestStatus.COMPLETED,
            ocr_result=ocr_result,
            llm_response=None,  # TODO: Implement actual LLM integration
            extracted_text=ocr_result.text,
            ai_explanation=ai_response,
            subject_detected="Geral",  # TODO: Implement subject detection
            confidence_score=ocr_result.confidence,
            processing_time_total=total_time,
            created_at=datetime.now(),
            user_id=current_user.id
        )
        
        # Update usage count
        current_user.usage_count += 1
        
        # Store result
        processing_requests[request_id] = result
        
        print(f"✅ Request {request_id} completed in {total_time:.2f}s")
        
        return ProcessingResponse(
            success=True,
            request_id=request_id,
            status=RequestStatus.COMPLETED,
            result=result,
            message="Processamento concluído com sucesso!"
        )
        
    except Exception as e:
        print(f"❌ Error processing request {request_id}: {str(e)}")
        
        return ProcessingResponse(
            success=False,
            request_id=request_id,
            status=RequestStatus.FAILED,
            error="PROCESSING_ERROR",
            message=f"Erro interno no processamento: {str(e)}"
        )

# Get processing result
@app.get("/process/{request_id}", response_model=ProcessingResponse)
async def get_processing_result(
    request_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get processing result by request ID"""
    
    if request_id not in processing_requests:
        raise HTTPException(
            status_code=404,
            detail="Request not found"
        )
    
    result = processing_requests[request_id]
    
    # Check if user owns this request
    if result.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )
    
    return ProcessingResponse(
        success=True,
        request_id=request_id,
        status=result.status,
        result=result,
        message="Resultado recuperado com sucesso"
    )

# List user's processing history
@app.get("/history")
async def get_processing_history(
    limit: int = 10,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get user's processing history"""
    
    user_requests = [
        result for result in processing_requests.values()
        if result.user_id == current_user.id
    ]
    
    # Sort by creation time (newest first)
    user_requests.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "requests": user_requests[:limit],
        "total": len(user_requests),
        "limit": limit
    }

# Plans information
@app.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    return {
        "plans": PLAN_FEATURES,
        "current_promotion": {
            "message": "🎉 Primeiros 100 usuários pagam 50% menos no primeiro mês!",
            "discount": 0.5,
            "expires": "2024-12-31"
        }
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": str(exc.detail),
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "Erro interno do servidor. Nossa equipe foi notificada.",
            "status_code": 500
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 