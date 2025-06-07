"""
Configuration settings for Academic Assistant SaaS Backend
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Configuration
    app_name: str = "Academic Assistant SaaS API"
    version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database Configuration (Supabase)
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str
    
    # OCR Services Configuration
    google_vision_api_key: Optional[str] = None
    azure_cv_endpoint: Optional[str] = None
    azure_cv_key: Optional[str] = None
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: str  # Free tier para início
    
    # OpenRouter Configuration (Fallback)
    openrouter_api_key: Optional[str] = None
    
    # Redis Configuration (Upstash)
    redis_url: Optional[str] = None
    
    # File Storage
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = ['.jpg', '.jpeg', '.png', '.pdf', '.webp']
    
    # Rate Limiting by Plan
    rate_limits: dict = {
        'free': {'requests_per_month': 10, 'requests_per_minute': 2},
        'pro': {'requests_per_month': 500, 'requests_per_minute': 10},
        'max': {'requests_per_month': -1, 'requests_per_minute': 20}  # -1 = unlimited
    }
    
    # CORS Configuration
    cors_origins: list = [
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://academicassistant.com.br",
        "https://www.academicassistant.com.br"
    ]
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Payment Configuration
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    mercadopago_access_token: Optional[str] = None
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Plan configuration
PLAN_FEATURES = {
    'free': {
        'name': 'Gratuito',
        'price': 0,
        'requests_per_month': 10,
        'ocr_quality': 'basic',
        'llm_model': 'groq-free',
        'features': ['OCR básico', 'IA básica', 'Acesso web'],
        'support': 'community'
    },
    'pro': {
        'name': 'Pro',
        'price': 19.90,
        'requests_per_month': 500,
        'ocr_quality': 'advanced',
        'llm_model': 'claude-haiku',
        'features': ['OCR avançado', 'IA premium', 'Todas as plataformas', 'Suporte prioritário'],
        'support': 'priority'
    },
    'max': {
        'name': 'Max',
        'price': 29.90,
        'requests_per_month': -1,  # Unlimited
        'ocr_quality': 'premium',
        'llm_model': 'claude-sonnet',
        'features': ['OCR premium', 'IA avançada', 'Todas as plataformas', 'Suporte VIP'],
        'support': 'vip'
    }
}

# LLM Model routing based on plan
LLM_ROUTING = {
    'free': {
        'primary': 'groq',
        'model': 'llama3-8b-8192',
        'fallback': None
    },
    'pro': {
        'primary': 'anthropic',
        'model': 'claude-3-haiku-20240307',
        'fallback': 'groq'
    },
    'max': {
        'primary': 'anthropic',
        'model': 'claude-3-sonnet-20240229',
        'fallback': 'claude-3-haiku-20240307'
    }
}

# OCR Service routing based on plan
OCR_ROUTING = {
    'free': ['tesseract'],
    'pro': ['google_vision', 'tesseract'],
    'max': ['google_vision', 'azure_cv', 'tesseract']
} 