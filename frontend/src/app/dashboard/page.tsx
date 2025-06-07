'use client'

import { useState, useRef, useEffect } from 'react'
import { Upload, Send, Image as ImageIcon, FileText, Zap, User, Settings, LogOut } from 'lucide-react'
import { useImageProcessing } from '@/hooks/useImageProcessing'
import { apiClient } from '@/lib/api'
import { UserProfile, UserUsage } from '../../../../shared/types'

export default function DashboardPage() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [question, setQuestion] = useState('')
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [userUsage, setUserUsage] = useState<UserUsage | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { processing, result, error, processImage, reset } = useImageProcessing()

  // Load user data on component mount
  useEffect(() => {
    const loadUserData = async () => {
      try {
        const [profile, usage] = await Promise.all([
          apiClient.getUserProfile(),
          apiClient.getUserUsage()
        ])
        setUserProfile(profile)
        setUserUsage(usage)
      } catch (error) {
        console.error('Failed to load user data:', error)
      }
    }

    loadUserData()
  }, [])

  // Default user data while loading
  const user = userProfile ? {
    name: userProfile.full_name || 'Usuário',
    email: userProfile.email,
    plan: userProfile.plan,
    usage: userUsage?.current_month_usage || 0,
    limit: userUsage?.plan_limit || 10
  } : {
    name: 'Carregando...',
    email: 'carregando...',
    plan: 'free' as const,
    usage: 0,
    limit: 10
  }

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string)
      }
      reader.readAsDataURL(file)
      reset() // Clear previous results
    }
  }

  const handleProcess = async () => {
    if (!selectedFile) return

    await processImage(selectedFile, question || undefined)
  }

  const handleAskQuestion = async () => {
    if (!question.trim() || !selectedFile) return

    await processImage(selectedFile, question)
    setQuestion('')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <FileText className="h-8 w-8 text-blue-600" />
                <span className="text-xl font-bold text-gray-900">Academic Assistant</span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Usage Badge */}
              <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                {user.usage}/{user.limit} consultas
              </div>

              {/* User Menu */}
              <div className="flex items-center space-x-2 text-gray-700">
                <User className="h-5 w-5" />
                <span className="hidden sm:block">{user.name}</span>
              </div>

              <button className="text-gray-500 hover:text-gray-700">
                <Settings className="h-5 w-5" />
              </button>

              <button className="text-gray-500 hover:text-gray-700">
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Panel - Image Upload */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                📸 Enviar Imagem
              </h2>

              {!selectedImage ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-gray-400 transition-colors"
                >
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 text-lg font-medium">
                    Clique para selecionar uma imagem
                  </p>
                  <p className="text-gray-500 text-sm mt-2">
                    PNG, JPG ou PDF até 10MB
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="relative">
                    <img
                      src={selectedImage}
                      alt="Uploaded"
                      className="w-full h-64 object-contain bg-gray-100 rounded-lg"
                    />
                    <button
                      onClick={() => setSelectedImage(null)}
                      className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-red-600"
                    >
                      ×
                    </button>
                  </div>

                  <button
                    onClick={handleProcess}
                    disabled={processing}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center"
                  >
                    {processing ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Processando...
                      </>
                    ) : (
                      <>
                        <Zap className="h-5 w-5 mr-2" />
                        Analisar com IA
                      </>
                    )}
                  </button>
                </div>
              )}

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.pdf"
                onChange={handleImageUpload}
                className="hidden"
              />
            </div>

            {/* Plan Info */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Plano {user.plan === 'free' ? 'Gratuito' : user.plan.toUpperCase()}
                  </h3>
                  <p className="text-gray-600">
                    {user.usage} de {user.limit} consultas utilizadas
                  </p>
                </div>

                {user.plan === 'free' && (
                  <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                    Upgrade
                  </button>
                )}
              </div>

              <div className="mt-4 bg-white rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(user.usage / user.limit) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Right Panel - Results */}
          <div className="space-y-6">
            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-red-900 mb-2">Erro no Processamento</h3>
                <p className="text-red-700">{error}</p>
              </div>
            )}

            {/* Extracted Text */}
            {result?.extracted_text && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <FileText className="h-5 w-5 mr-2 text-green-600" />
                  Texto Extraído
                </h3>
                <pre className="bg-gray-100 p-4 rounded-lg text-sm font-mono whitespace-pre-wrap">
                  {result.extracted_text}
                </pre>
              </div>
            )}

            {/* AI Response */}
            {result?.ai_explanation && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Zap className="h-5 w-5 mr-2 text-purple-600" />
                  Explicação da IA
                </h3>
                <div className="prose prose-sm max-w-none">
                  <div className="whitespace-pre-wrap text-gray-700">
                    {result.ai_explanation}
                  </div>
                </div>
              </div>
            )}

            {/* Question Input */}
            {result?.extracted_text && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  💬 Faça uma pergunta
                </h3>
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ex: Como resolver esta equação passo a passo?"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyPress={(e) => e.key === 'Enter' && handleAskQuestion()}
                    aria-label="Digite sua pergunta"
                  />
                  <button
                    onClick={handleAskQuestion}
                    disabled={processing || !question.trim()}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md transition-colors flex items-center"
                    aria-label="Enviar pergunta"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Getting Started */}
            {!selectedImage && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  🚀 Como começar
                </h3>
                <div className="space-y-3 text-gray-600">
                  <div className="flex items-start space-x-3">
                    <span className="bg-blue-100 text-blue-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium">1</span>
                    <p>Envie uma foto do seu exercício ou problema</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <span className="bg-blue-100 text-blue-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium">2</span>
                    <p>Nossa IA extrairá o texto automaticamente</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <span className="bg-blue-100 text-blue-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium">3</span>
                    <p>Receba explicações detalhadas e faça perguntas</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 