// Shared types between frontend and backend
// Keep in sync with backend/models.py

export type PlanType = 'free' | 'pro' | 'max'

export type SubscriptionStatus = 'active' | 'inactive' | 'canceled' | 'past_due'

export type RequestStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type OCRProvider = 'tesseract' | 'google_vision' | 'azure_cv'

export type LLMProvider = 'groq' | 'anthropic' | 'openai' | 'openrouter'

export interface UserProfile {
  id: string
  email: string
  full_name?: string
  username?: string
  avatar_url?: string
  plan: PlanType
  subscription_status: SubscriptionStatus
  usage_count: number
  usage_month: number
  usage_reset_date?: string
  created_at: string
  updated_at?: string
}

export interface ImageUploadRequest {
  image_data: string // Base64 encoded
  question?: string
  subject?: string
}

export interface OCRResult {
  provider: OCRProvider
  text: string
  confidence?: number
  processing_time: number
  success: boolean
  error?: string
}

export interface LLMResponse {
  provider: LLMProvider
  model: string
  response: string
  tokens_used?: number
  processing_time: number
  success: boolean
  error?: string
}

export interface ProcessingResult {
  request_id: string
  status: RequestStatus
  ocr_result?: OCRResult
  llm_response?: LLMResponse
  extracted_text?: string
  ai_explanation?: string
  subject_detected?: string
  confidence_score?: number
  processing_time_total: number
  created_at: string
  user_id: string
}

export interface ProcessingResponse {
  success: boolean
  request_id: string
  status: RequestStatus
  result?: ProcessingResult
  error?: string
  message: string
}

export interface UserUsage {
  user_id: string
  current_month_usage: number
  plan_limit: number
  remaining_requests: number
  reset_date: string
  plan: PlanType
}

export interface RateLimitInfo {
  requests_remaining: number
  reset_time: string
  plan_limit: number
  current_usage: number
}

export interface PlanConfig {
  name: string
  price: number
  requests_per_month: number
  ocr_quality: string
  llm_model: string
  features: string[]
  support: string
}

export interface ErrorResponse {
  error: string
  message: string
  details?: Record<string, any>
  request_id?: string
}

export interface HealthCheck {
  status: string
  version: string
  timestamp: string
  services: Record<string, boolean>
  uptime: number
} 