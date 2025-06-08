import { useState, useCallback } from 'react'

interface ProcessingResult {
  text: string
  confidence: number
  processing_time: number
}

interface UseImageProcessingReturn {
  processImage: (file: File) => Promise<void>
  isProcessing: boolean
  result: ProcessingResult | null
  error: string | null
  reset: () => void
}

export const useImageProcessing = (): UseImageProcessingReturn => {
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const processImage = useCallback(async (file: File) => {
    setIsProcessing(true)
    setError(null)
    setResult(null)

    try {
      // Convert file to base64
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          const result = reader.result as string
          // Remove data:image/...;base64, prefix
          const base64Data = result.split(',')[1]
          resolve(base64Data)
        }
        reader.onerror = reject
        reader.readAsDataURL(file)
      })

      // Make API call
      const response = await fetch('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || 'demo-token'}`
        },
        body: JSON.stringify({
          image_data: base64
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Processing failed')
      }

      if (data.success) {
        setResult(data.data)
      } else {
        throw new Error(data.error || 'Processing failed')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
    } finally {
      setIsProcessing(false)
    }
  }, [])

  const reset = useCallback(() => {
    setIsProcessing(false)
    setResult(null)
    setError(null)
  }, [])

  return {
    processImage,
    isProcessing,
    result,
    error,
    reset
  }
} 