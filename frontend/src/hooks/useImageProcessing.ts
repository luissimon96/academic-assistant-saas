'use client'

import { useState, useCallback } from 'react'
import { apiClient } from '@/lib/api'
import { ProcessingResponse, ProcessingResult } from '../../../shared/types'

interface UseImageProcessingResult {
  processing: boolean
  result: ProcessingResult | null
  error: string | null
  processImage: (file: File, question?: string, subject?: string) => Promise<void>
  reset: () => void
}

export function useImageProcessing(): UseImageProcessingResult {
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const processImage = useCallback(async (
    file: File,
    question?: string,
    subject?: string
  ) => {
    try {
      setProcessing(true)
      setError(null)
      setResult(null)

      // Convert file to base64
      const imageData = await apiClient.fileToBase64(file)

      // Send request
      const response: ProcessingResponse = await apiClient.processImage({
        image_data: imageData,
        question,
        subject
      })

      if (response.success && response.result) {
        setResult(response.result)
      } else {
        setError(response.message || 'Processing failed')
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
    } finally {
      setProcessing(false)
    }
  }, [])

  const reset = useCallback(() => {
    setProcessing(false)
    setResult(null)
    setError(null)
  }, [])

  return {
    processing,
    result,
    error,
    processImage,
    reset
  }
} 