import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'
import { AuthField } from '@/components/auth/auth-field'
import { AuthLayout } from '@/components/auth/auth-layout'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/use-auth'
import { loginRequest } from '@/lib/auth-api'

const loginSchema = z.object({
  email: z.email('Informe um e-mail válido'),
  password: z.string().min(1, 'Informe sua senha'),
})

type LoginValues = z.infer<typeof loginSchema>

export function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [formError, setFormError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) })

  const mutation = useMutation({
    mutationFn: loginRequest,
    onSuccess: (token) => {
      login(token.access_token)
      navigate('/', { replace: true })
    },
    onError: (error) => {
      if (isAxiosError(error) && error.response?.status === 401) {
        setFormError('E-mail ou senha inválidos.')
      } else {
        setFormError('Não foi possível entrar. Tente novamente.')
        toast.error('Erro de conexão com o servidor.')
      }
    },
  })

  function onSubmit(values: LoginValues) {
    setFormError(null)
    mutation.mutate(values)
  }

  return (
    <AuthLayout>
      <h2 className="text-2xl font-bold tracking-tight text-foreground">
        Bem-vindo de volta
      </h2>
      <p className="mt-1.5 text-sm text-muted-foreground">
        Acesse sua conta para continuar
      </p>

      <form className="mt-8 space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
        {formError && (
          <p
            role="alert"
            className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {formError}
          </p>
        )}

        <AuthField
          id="email"
          type="email"
          label="E-mail"
          autoComplete="email"
          placeholder="ana@taskly.app"
          error={errors.email?.message}
          {...register('email')}
        />

        <AuthField
          id="password"
          type="password"
          label="Senha"
          autoComplete="current-password"
          placeholder="••••••••"
          error={errors.password?.message}
          labelAside={
            <button
              type="button"
              onClick={() => toast('Recuperação de senha chega em breve.')}
              className="text-xs font-medium text-brand-600 hover:underline"
            >
              Esqueceu a senha?
            </button>
          }
          {...register('password')}
        />

        <Button
          type="submit"
          disabled={mutation.isPending}
          className="h-10 w-full bg-gradient-to-r from-brand-500 to-brand-700 text-sm hover:from-brand-600 hover:to-brand-800"
        >
          {mutation.isPending ? 'Entrando…' : 'Entrar'}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Não tem conta?{' '}
        <Link to="/register" className="font-semibold text-brand-600 hover:underline">
          Criar conta grátis
        </Link>
      </p>
    </AuthLayout>
  )
}
