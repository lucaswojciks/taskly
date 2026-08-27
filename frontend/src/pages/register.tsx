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
import { loginRequest, registerRequest } from '@/lib/auth-api'

const registerSchema = z
  .object({
    email: z.email('Informe um e-mail válido'),
    password: z
      .string()
      .min(8, 'A senha deve ter ao menos 8 caracteres')
      .max(72, 'A senha deve ter no máximo 72 caracteres'),
    confirmPassword: z.string().min(1, 'Confirme sua senha'),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'As senhas não coincidem',
    path: ['confirmPassword'],
  })

type RegisterValues = z.infer<typeof registerSchema>

export function RegisterPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [formError, setFormError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) })

  const mutation = useMutation({
    mutationFn: async ({ email, password }: RegisterValues) => {
      await registerRequest({ email, password })
      // auto-login right after a successful registration
      return loginRequest({ email, password })
    },
    onSuccess: (token) => {
      login(token.access_token)
      navigate('/', { replace: true })
    },
    onError: (error) => {
      if (isAxiosError(error) && error.response?.status === 409) {
        setFormError('Este e-mail já está cadastrado.')
      } else if (isAxiosError(error) && error.response?.status === 422) {
        setFormError('Verifique os dados informados e tente novamente.')
      } else {
        setFormError('Não foi possível criar a conta. Tente novamente.')
        toast.error('Erro de conexão com o servidor.')
      }
    },
  })

  function onSubmit(values: RegisterValues) {
    setFormError(null)
    mutation.mutate(values)
  }

  return (
    <AuthLayout>
      <h2 className="text-2xl font-bold tracking-tight text-foreground">
        Criar sua conta
      </h2>
      <p className="mt-1.5 text-sm text-muted-foreground">
        Comece a organizar suas tarefas hoje
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
          autoComplete="new-password"
          placeholder="Mínimo de 8 caracteres"
          error={errors.password?.message}
          {...register('password')}
        />

        <AuthField
          id="confirmPassword"
          type="password"
          label="Confirmar senha"
          autoComplete="new-password"
          placeholder="Repita a senha"
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />

        <Button
          type="submit"
          disabled={mutation.isPending}
          className="h-10 w-full bg-gradient-to-r from-brand-500 to-brand-700 text-sm hover:from-brand-600 hover:to-brand-800"
        >
          {mutation.isPending ? 'Criando conta…' : 'Criar conta grátis'}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Já tem conta?{' '}
        <Link to="/login" className="font-semibold text-brand-600 hover:underline">
          Entrar
        </Link>
      </p>
    </AuthLayout>
  )
}
