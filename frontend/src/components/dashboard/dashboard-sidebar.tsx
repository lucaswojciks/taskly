import { useNavigate } from 'react-router-dom'
import {
  LayoutGridIcon,
  LogOutIcon,
  PlusIcon,
  SquareCheckBigIcon,
} from 'lucide-react'
import { NewProjectDialog } from '@/components/dashboard/new-project-dialog'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth, useCurrentUser } from '@/hooks/use-auth'
import { useProjects } from '@/hooks/use-projects'
import { projectColor } from '@/lib/colors'
import { cn } from '@/lib/utils'

interface DashboardSidebarProps {
  selectedProjectId: string | null
  onSelectProject: (projectId: string) => void
}

export function DashboardSidebar({
  selectedProjectId,
  onSelectProject,
}: DashboardSidebarProps) {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const { data: user } = useCurrentUser()
  const { data: projects = [], isLoading } = useProjects()

  const email = user?.email ?? ''
  const initial = email.charAt(0).toUpperCase() || '?'

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r bg-sidebar">
      <div className="flex h-16 items-center gap-2 border-b px-5">
        <span className="flex size-8 items-center justify-center rounded-lg bg-navy-900 text-white">
          <SquareCheckBigIcon className="size-4" />
        </span>
        <span className="text-lg font-bold text-navy-900">Taskly</span>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            className="flex items-center gap-3 border-b px-5 py-4 text-left transition-colors hover:bg-muted/50"
          >
            <Avatar>
              <AvatarFallback className="bg-brand-100 font-semibold text-brand-700">
                {initial}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-foreground">
                {email || '…'}
              </p>
              <p className="text-xs text-muted-foreground">Minha conta</p>
            </div>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          <DropdownMenuLabel className="truncate font-normal text-muted-foreground">
            {email}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout}>
            <LogOutIcon className="size-4" />
            Sair
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <div className="px-3 py-3">
        <div className="flex items-center gap-2.5 rounded-lg bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700">
          <LayoutGridIcon className="size-4" />
          Visão geral
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-3">
        <p className="px-3 py-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          Projetos
        </p>

        {isLoading ? (
          <p className="px-3 text-xs text-muted-foreground">Carregando…</p>
        ) : projects.length === 0 ? (
          <p className="px-3 text-xs text-muted-foreground">Nenhum projeto ainda.</p>
        ) : (
          <ul className="space-y-0.5">
            {projects.map((project) => {
              const active = project.id === selectedProjectId
              return (
                <li key={project.id}>
                  <button
                    type="button"
                    onClick={() => onSelectProject(project.id)}
                    className={cn(
                      'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors',
                      active
                        ? 'bg-brand-50 font-semibold text-brand-800'
                        : 'text-foreground hover:bg-muted/60',
                    )}
                  >
                    <span
                      className="size-2 shrink-0 rounded-full"
                      style={{ backgroundColor: projectColor(project.id) }}
                    />
                    <span className="flex-1 truncate text-left">{project.name}</span>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      <div className="border-t p-3">
        <NewProjectDialog onCreated={onSelectProject}>
          <button
            type="button"
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-border py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:border-brand-300 hover:text-brand-700"
          >
            <PlusIcon className="size-4" />
            Novo projeto
          </button>
        </NewProjectDialog>
      </div>
    </aside>
  )
}
