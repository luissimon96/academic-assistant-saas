'use client'

import { useState } from 'react'
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { supabase } from '@/lib/supabase'

interface AuthFormProps {
  view?: 'sign_in' | 'sign_up'
}

export default function AuthForm({ view = 'sign_in' }: AuthFormProps) {
  const [loading, setLoading] = useState(false)

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white p-8 rounded-lg shadow-lg border">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">
            {view === 'sign_in' ? 'Entrar' : 'Criar Conta'}
          </h1>
          <p className="text-gray-600 mt-2">
            {view === 'sign_in'
              ? 'Acesse sua conta do Academic Assistant'
              : 'Crie sua conta e comece a usar gratuitamente'
            }
          </p>
        </div>

        <Auth
          supabaseClient={supabase}
          appearance={{
            theme: ThemeSupa,
            variables: {
              default: {
                colors: {
                  brand: '#3b82f6',
                  brandAccent: '#2563eb',
                  brandButtonText: 'white',
                  defaultButtonBackground: '#f3f4f6',
                  defaultButtonBackgroundHover: '#e5e7eb',
                }
              }
            },
            className: {
              container: 'w-full',
              button: 'w-full px-4 py-2 rounded-md font-medium transition-colors',
              input: 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
              label: 'block text-sm font-medium text-gray-700 mb-1',
            }
          }}
          view={view}
          providers={['google']}
          redirectTo={`${window.location.origin}/dashboard`}
          localization={{
            variables: {
              sign_in: {
                email_label: 'Email',
                password_label: 'Senha',
                button_label: 'Entrar',
                loading_button_label: 'Entrando...',
                social_provider_text: 'Continuar com {{provider}}',
                link_text: 'Já tem uma conta? Entre aqui',
                confirmation_text: 'Verifique seu email para confirmar o login'
              },
              sign_up: {
                email_label: 'Email',
                password_label: 'Senha',
                button_label: 'Criar conta',
                loading_button_label: 'Criando conta...',
                social_provider_text: 'Continuar com {{provider}}',
                link_text: 'Não tem uma conta? Crie aqui',
                confirmation_text: 'Verifique seu email para confirmar o cadastro'
              }
            }
          }}
        />

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Ao criar uma conta, você concorda com nossos{' '}
            <a href="/terms" className="text-blue-600 hover:underline">
              Termos de Uso
            </a>{' '}
            e{' '}
            <a href="/privacy" className="text-blue-600 hover:underline">
              Política de Privacidade
            </a>
          </p>
        </div>
      </div>
    </div>
  )
} 