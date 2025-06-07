import AuthForm from '@/components/auth/AuthForm'

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <AuthForm view="sign_in" />

        <div className="text-center mt-6">
          <p className="text-gray-600">
            Não tem uma conta?{' '}
            <a href="/register" className="text-blue-600 hover:underline font-medium">
              Criar conta grátis
            </a>
          </p>
        </div>
      </div>
    </div>
  )
} 