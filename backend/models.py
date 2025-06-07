"""
Pydantic models for Academic Assistant SaaS Backend
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

# Enums
class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    MAX = "max"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELED = "canceled"
    PAST_DUE = "past_due"

class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class OCRProvider(str, Enum):
    TESSERACT = "tesseract"
    GOOGLE_VISION = "google_vision"
    AZURE_CV = "azure_cv"

class LLMProvider(str, Enum):
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENROUTER = "openrouter"

# Request/Response Models
class ImageUploadRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image data")
    question: Optional[str] = Field(None, description="Specific question about the image")
    subject: Optional[str] = Field(None, description="Subject area (math, physics, etc.)")

class OCRResult(BaseModel):
    provider: OCRProvider
    text: str
    confidence: Optional[float] = None
    processing_time: float
    success: bool = True
    error: Optional[str] = None

class LLMResponse(BaseModel):
    provider: LLMProvider
    model: str
    response: str
    tokens_used: Optional[int] = None
    processing_time: float
    success: bool = True
    error: Optional[str] = None

class ProcessingResult(BaseModel):
    request_id: str
    status: RequestStatus
    ocr_result: Optional[OCRResult] = None
    llm_response: Optional[LLMResponse] = None
    extracted_text: Optional[str] = None
    ai_explanation: Optional[str] = None
    subject_detected: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time_total: float
    created_at: datetime
    user_id: str

class ProcessingResponse(BaseModel):
    success: bool
    request_id: str
    status: RequestStatus
    result: Optional[ProcessingResult] = None
    error: Optional[str] = None
    message: str

# User Models
class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    plan: PlanType = PlanType.FREE
    subscription_status: SubscriptionStatus = SubscriptionStatus.INACTIVE
    usage_count: int = 0
    usage_month: int = 0
    usage_reset_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserUsage(BaseModel):
    user_id: str
    current_month_usage: int
    plan_limit: int
    remaining_requests: int
    reset_date: datetime
    plan: PlanType

class SubscriptionUpdate(BaseModel):
    plan: PlanType
    status: SubscriptionStatus
    stripe_subscription_id: Optional[str] = None
    mercadopago_subscription_id: Optional[str] = None

# Analytics Models
class UsageAnalytics(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_processing_time: float
    most_used_subjects: List[str]
    ocr_accuracy: float
    user_satisfaction: Optional[float] = None

class SystemMetrics(BaseModel):
    active_users: int
    total_requests_today: int
    avg_response_time: float
    error_rate: float
    popular_plans: Dict[str, int]
    revenue_monthly: float

# Configuration Models
class PlanConfig(BaseModel):
    name: str
    price: float
    requests_per_month: int
    ocr_quality: str
    llm_model: str
    features: List[str]
    support: str

class RateLimitInfo(BaseModel):
    requests_remaining: int
    reset_time: datetime
    plan_limit: int
    current_usage: int

# Error Models
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

class ValidationError(BaseModel):
    field: str
    message: str
    value: Any

# Health Check
class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, bool]
    uptime: float

# Payment Models
class PaymentIntent(BaseModel):
    amount: float
    currency: str = "BRL"
    plan: PlanType
    payment_method: str  # stripe, mercadopago
    return_url: Optional[str] = None

class PaymentResult(BaseModel):
    success: bool
    payment_id: str
    status: str
    checkout_url: Optional[str] = None
    error: Optional[str] = None

# Webhook Models
class StripeWebhook(BaseModel):
    type: str
    data: Dict[str, Any]

class MercadoPagoWebhook(BaseModel):
    action: str
    api_version: str
    data: Dict[str, Any] 