import {
  ProcessingResponse,
  ImageUploadRequest,
  UserProfile,
  UserUsage,
  PlanConfig
} from '../../../shared/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class APIClient {
  private baseURL: string
  private defaultHeaders: HeadersInit

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`

    const config: RequestInit = {
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
      ...options,
    }

    // Add auth token if available
    const token = this.getAuthToken()
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      }
    }

    const response = await fetch(url, config)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  private getAuthToken(): string | null {
    // For now, return a mock token. In production, get from Supabase
    return 'mock-jwt-token'
  }

  // Health check
  async healthCheck() {
    return this.request('/health')
  }

  // User endpoints
  async getUserProfile(): Promise<UserProfile> {
    return this.request('/user/profile')
  }

  async getUserUsage(): Promise<UserUsage> {
    return this.request('/user/usage')
  }

  // Processing endpoints
  async processImage(request: ImageUploadRequest): Promise<ProcessingResponse> {
    return this.request('/process', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getProcessingResult(requestId: string): Promise<ProcessingResponse> {
    return this.request(`/process/${requestId}`)
  }

  async getProcessingHistory(limit: number = 10) {
    return this.request(`/history?limit=${limit}`)
  }

  // Plans
  async getPlans(): Promise<{ plans: Record<string, PlanConfig> }> {
    return this.request('/plans')
  }

  // Utility method to convert file to base64
  fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => {
        const result = reader.result as string
        // Remove data:image/xxx;base64, prefix
        const base64 = result.split(',')[1]
        resolve(base64)
      }
      reader.onerror = error => reject(error)
    })
  }
}

export const apiClient = new APIClient()
export default apiClient 