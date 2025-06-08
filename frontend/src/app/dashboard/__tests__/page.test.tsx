import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import DashboardPage from '../page'

// Mocks
const mockPush = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

jest.mock('@/hooks/useImageProcessing', () => ({
  useImageProcessing: () => ({
    processImage: jest.fn(),
    isProcessing: false,
    result: null,
    error: null,
    reset: jest.fn(),
  }),
}))

describe('DashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render dashboard components', () => {
    render(<DashboardPage />)

    expect(screen.getByText('Academic Assistant')).toBeInTheDocument()
    expect(screen.getByText('Faça upload de uma imagem')).toBeInTheDocument()
    expect(screen.getByText('Sair')).toBeInTheDocument()
  })

  it('should handle file upload', () => {
    render(<DashboardPage />)

    const fileInput = screen.getByLabelText(/escolher arquivo/i)
    const file = new File(['image content'], 'test.png', { type: 'image/png' })

    fireEvent.change(fileInput, { target: { files: [file] } })

    expect(fileInput.files?.[0]).toBe(file)
  })

  it('should handle logout', () => {
    render(<DashboardPage />)

    const logoutButton = screen.getByText('Sair')
    fireEvent.click(logoutButton)

    expect(mockPush).toHaveBeenCalledWith('/')
  })
}) 