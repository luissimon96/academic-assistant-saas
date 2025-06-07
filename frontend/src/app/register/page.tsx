import AuthForm from '@/components/auth/AuthForm'

export default function RegisterPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <AuthForm view="sign_up" />

        <div className="text-center mt-6">
          <p className="text-gray-600">
            Já tem uma conta?{' '}
            <a href="/login" className="text-blue-600 hover:underline font-medium">
              Fazer login
            </a>
          </p>
        </div>
      </div>
    </div>
  )
} 