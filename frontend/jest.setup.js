import '@testing-library/jest-dom'

// Mock de APIs do navegador
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock de File e FileReader para testes de upload
global.File = class MockFile {
  constructor(parts, filename, properties) {
    this.parts = parts
    this.name = filename
    this.properties = properties
  }
}

global.FileReader = class MockFileReader {
  constructor() {
    this.result = null
    this.onload = null
    this.onerror = null
  }
  
  readAsDataURL(file) {
    setTimeout(() => {
      this.result = 'data:image/png;base64,mock-image-data'
      if (this.onload) this.onload({ target: this })
    }, 0)
  }
}

// Suppress console warnings in tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
}) 