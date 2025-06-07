import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import DashboardPage from '../page'

// Mock do useRouter
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock do hook useImageProcessing
jest.mock('../../hooks/useImageProcessing', () => ({
  useImageProcessing: () => ({
    isProcessing: false,
    result: null,
    error: null,
    processImage: jest.fn(),
    reset: jest.fn(),
  }),
}))

const mockPush = jest.fn()

describe('DashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
      ; (useRouter as jest.Mock).mockReturnValue({
        push: mockPush,
      })
  })

  it('should render dashboard components', () => {
    render(<DashboardPage />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Upload de Imagem')).toBeInTheDocument()
    expect(screen.getByText('Selecione uma imagem para análise')).toBeInTheDocument()
  })

  it('should handle file upload', async () => {
    render(<DashboardPage />)

    const fileInput = screen.getByLabelText(/upload/i)
    const file = new File(['image content'], 'test.png', { type: 'image/png' })

    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(fileInput.files?.[0]).toBe(file)
    })
  })

  it('should display upload area with proper styling', () => {
    render(<DashboardPage />)

    const uploadArea = screen.getByRole('button', { name: /clique para selecionar/i })
    expect(uploadArea).toBeInTheDocument()
    expect(uploadArea).toHaveClass('border-dashed')
  })

  it('should show processing state when image is being processed', () => {
    // Mock hook with processing state
    const mockUseImageProcessing = require('../../hooks/useImageProcessing')
    mockUseImageProcessing.useImageProcessing.mockReturnValue({
      isProcessing: true,
      result: null,
      error: null,
      processImage: jest.fn(),
      reset: jest.fn(),
    })

    render(<DashboardPage />)

    expect(screen.getByText(/processando/i)).toBeInTheDocument()
  })

  it('should display results when processing is complete', () => {
    // Mock hook with results
    const mockUseImageProcessing = require('../../hooks/useImageProcessing')
    mockUseImageProcessing.useImageProcessing.mockReturnValue({
      isProcessing: false,
      result: {
        text: 'Extracted text from image',
        confidence: 0.95,
        processing_time: 1.2
      },
      error: null,
      processImage: jest.fn(),
      reset: jest.fn(),
    })

    render(<DashboardPage />)

    expect(screen.getByText('Extracted text from image')).toBeInTheDocument()
    expect(screen.getByText(/95%/)).toBeInTheDocument()
  })

  it('should display error when processing fails', () => {
    // Mock hook with error
    const mockUseImageProcessing = require('../../hooks/useImageProcessing')
    mockUseImageProcessing.useImageProcessing.mockReturnValue({
      isProcessing: false,
      result: null,
      error: 'Processing failed',
      processImage: jest.fn(),
      reset: jest.fn(),
    })

    render(<DashboardPage />)

    expect(screen.getByText('Processing failed')).toBeInTheDocument()
  })

  it('should have logout functionality', () => {
    render(<DashboardPage />)

    const logoutButton = screen.getByRole('button', { name: /sair/i })
    fireEvent.click(logoutButton)

    expect(mockPush).toHaveBeenCalledWith('/')
  })
}) 