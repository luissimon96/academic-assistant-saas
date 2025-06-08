import { renderHook, act } from '@testing-library/react'
import { useImageProcessing } from '../useImageProcessing'

// Mock do fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('useImageProcessing', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useImageProcessing())

    expect(result.current.isProcessing).toBe(false)
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('should handle successful image processing', async () => {
    const mockResponse = {
      success: true,
      data: {
        text: 'Extracted text',
        confidence: 0.95,
        processing_time: 1.2
      }
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })

    const { result } = renderHook(() => useImageProcessing())
    const mockFile = new File(['image content'], 'test.png', { type: 'image/png' })

    await act(async () => {
      await result.current.processImage(mockFile)
    })

    expect(result.current.isProcessing).toBe(false)
    expect(result.current.result).toEqual(mockResponse.data)
    expect(result.current.error).toBeNull()
  })

  it('should handle processing errors', async () => {
    const mockError = { error: 'Processing failed' }

    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => mockError
    })

    const { result } = renderHook(() => useImageProcessing())
    const mockFile = new File(['image content'], 'test.png', { type: 'image/png' })

    await act(async () => {
      await result.current.processImage(mockFile)
    })

    expect(result.current.isProcessing).toBe(false)
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBe('Processing failed')
  })

  it('should handle network errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useImageProcessing())
    const mockFile = new File(['image content'], 'test.png', { type: 'image/png' })

    await act(async () => {
      await result.current.processImage(mockFile)
    })

    expect(result.current.isProcessing).toBe(false)
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBe('Network error')
  })

  it('should reset state when called', () => {
    const { result } = renderHook(() => useImageProcessing())

    act(() => {
      result.current.reset()
    })

    expect(result.current.isProcessing).toBe(false)
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBeNull()
  })
}) 