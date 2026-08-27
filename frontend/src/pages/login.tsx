import { Link } from 'react-router-dom'
import { SquareCheckBigIcon } from 'lucide-react'

export function LoginPage() {
  return (
    <div className="grid min-h-svh place-items-center bg-navy-900 p-6">
      <div className="w-full max-w-sm rounded-2xl bg-card p-8 text-card-foreground shadow-card">
        <div className="flex items-center gap-2 text-navy-900">
          <span className="flex size-8 items-center justify-center rounded-lg bg-navy-900 text-white">
            <SquareCheckBigIcon className="size-4" />
          </span>
          <span className="text-lg font-bold">Taskly</span>
        </div>
        <h1 className="mt-6 text-xl font-semibold">Bem-vindo de volta</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Tela de login — em construção.
        </p>
        <p className="mt-6 text-sm text-muted-foreground">
          Não tem conta?{' '}
          <Link to="/register" className="font-semibold text-brand-600 hover:underline">
            Criar conta grátis
          </Link>
        </p>
      </div>
    </div>
  )
}
