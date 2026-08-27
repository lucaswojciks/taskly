import { useNavigate } from 'react-router-dom'
import { SquareCheckBigIcon } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/use-auth'

export function HomePage() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="grid min-h-svh place-items-center bg-background p-6">
      <div className="w-full max-w-md rounded-2xl border bg-card p-10 text-center shadow-card">
        <div className="mx-auto flex size-12 items-center justify-center rounded-xl bg-navy-900 text-white">
          <SquareCheckBigIcon className="size-6" />
        </div>

        <h1 className="mt-5 text-2xl font-bold tracking-tight text-foreground">
          Hello Taskly
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Esqueleto do frontend rodando — roteamento, tema petróleo/índigo, TanStack
          Query e client HTTP prontos.
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          <Badge className="border-transparent bg-status-neutral-soft text-status-neutral">
            Não iniciada
          </Badge>
          <Badge className="border-transparent bg-status-progress-soft text-status-progress">
            Em andamento
          </Badge>
          <Badge className="border-transparent bg-status-done-soft text-status-done">
            Concluída
          </Badge>
          <Badge className="border-transparent bg-status-cancelled-soft text-status-cancelled line-through">
            Cancelada
          </Badge>
        </div>

        <Button variant="outline" className="mt-8 w-full" onClick={handleLogout}>
          Sair
        </Button>
      </div>
    </div>
  )
}
