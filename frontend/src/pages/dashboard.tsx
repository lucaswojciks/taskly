import { useState } from 'react'
import { FolderPlusIcon, LayoutGridIcon, ListIcon, MenuIcon } from 'lucide-react'
import {
  DashboardSidebar,
  SidebarNav,
} from '@/components/dashboard/dashboard-sidebar'
import { NewProjectDialog } from '@/components/dashboard/new-project-dialog'
import { NewTaskDialog } from '@/components/dashboard/new-task-dialog'
import { StatusSummary } from '@/components/dashboard/status-summary'
import { TaskDetailSheet } from '@/components/dashboard/task-detail-sheet'
import { QueryError } from '@/components/query-error'
import { TaskKanbanView } from '@/components/tasks/task-kanban-view'
import { TaskListView } from '@/components/tasks/task-list-view'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useProjects } from '@/hooks/use-projects'
import { useProjectTasks } from '@/hooks/use-tasks'

type View = 'list' | 'kanban'

export function DashboardPage() {
  const {
    data: projects = [],
    isLoading: projectsLoading,
    isError: projectsIsError,
    isPaused: projectsIsPaused,
    refetch: refetchProjects,
  } = useProjects()
  // A network failure (server unreachable) leaves the query `paused` rather
  // than `error`, so treat both as "couldn't load" for the user.
  const projectsError = projectsIsError || projectsIsPaused

  const [pickedProjectId, setPickedProjectId] = useState<string | null>(null)
  const selectedProjectId = pickedProjectId ?? projects[0]?.id ?? null
  const selectedProject =
    projects.find((project) => project.id === selectedProjectId) ?? null

  const {
    data: tasks = [],
    isLoading: tasksLoading,
    isError: tasksIsError,
    isPaused: tasksIsPaused,
    refetch: refetchTasks,
  } = useProjectTasks(selectedProjectId)
  const tasksError = tasksIsError || tasksIsPaused

  const [view, setView] = useState<View>('list')
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  // Derived from the list so edits/deletes in the sheet reflect immediately
  // (and the sheet closes on its own when the task is removed).
  const [openTaskId, setOpenTaskId] = useState<string | null>(null)
  const openTask = tasks.find((task) => task.id === openTaskId) ?? null

  const doneCount = tasks.filter((task) => task.status === 'done').length

  return (
    <div className="flex h-svh overflow-hidden bg-background">
      <DashboardSidebar
        selectedProjectId={selectedProjectId}
        onSelectProject={setPickedProjectId}
      />

      <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
        <SheetContent side="left" className="w-72 p-0" showCloseButton={false}>
          <SheetHeader className="sr-only">
            <SheetTitle>Menu de projetos</SheetTitle>
            <SheetDescription>Selecione um projeto ou crie um novo.</SheetDescription>
          </SheetHeader>
          <SidebarNav
            selectedProjectId={selectedProjectId}
            onSelectProject={setPickedProjectId}
            onNavigate={() => setMobileSidebarOpen(false)}
          />
        </SheetContent>
      </Sheet>

      <main className="flex flex-1 flex-col overflow-hidden">
        {projectsLoading ? (
          <div className="grid flex-1 place-items-center text-sm text-muted-foreground">
            Carregando…
          </div>
        ) : projectsError ? (
          <div className="flex flex-1 items-center justify-center p-6">
            <QueryError
              message="Não foi possível carregar seus projetos."
              onRetry={() => void refetchProjects()}
              className="max-w-sm"
            />
          </div>
        ) : projects.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
            <span className="flex size-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
              <FolderPlusIcon className="size-7" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                Crie seu primeiro projeto
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Organize suas tarefas agrupando-as em projetos.
              </p>
            </div>
            <NewProjectDialog onCreated={setPickedProjectId}>
              <Button className="bg-gradient-to-r from-brand-500 to-brand-700 hover:from-brand-600 hover:to-brand-800">
                <FolderPlusIcon className="size-4" />
                Novo projeto
              </Button>
            </NewProjectDialog>
          </div>
        ) : (
          <Tabs
            value={view}
            onValueChange={(next) => setView(next as View)}
            className="flex flex-1 flex-col gap-0 overflow-hidden"
          >
            <header className="flex flex-col gap-3 border-b px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:py-4 lg:px-8">
              <div className="flex min-w-0 items-center gap-1.5">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label="Abrir menu de projetos"
                  className="-ml-1 shrink-0 lg:hidden"
                  onClick={() => setMobileSidebarOpen(true)}
                >
                  <MenuIcon className="size-5" />
                </Button>
                <div className="min-w-0">
                  <h1 className="truncate text-lg font-bold tracking-tight text-foreground sm:text-xl">
                    {selectedProject?.name}
                  </h1>
                  <p className="text-xs text-muted-foreground">
                    {tasks.length} {tasks.length === 1 ? 'tarefa' : 'tarefas'}
                    {' · '}
                    {doneCount} {doneCount === 1 ? 'concluída' : 'concluídas'}
                  </p>
                </div>
              </div>

              <div className="flex shrink-0 items-center justify-between gap-2 sm:justify-end sm:gap-3">
                <TabsList>
                  <TabsTrigger value="list">
                    <ListIcon className="size-4" />
                    Lista
                  </TabsTrigger>
                  <TabsTrigger value="kanban">
                    <LayoutGridIcon className="size-4" />
                    Kanban
                  </TabsTrigger>
                </TabsList>
                {selectedProjectId && <NewTaskDialog projectId={selectedProjectId} />}
              </div>
            </header>

            <div className="border-b px-4 py-3 sm:px-6 sm:py-4 lg:px-8">
              <StatusSummary tasks={tasks} />
            </div>

            <div className="flex-1 overflow-hidden">
              <TabsContent
                value="list"
                className="mt-0 h-full overflow-y-auto px-4 py-5 sm:px-6 lg:px-8 lg:py-6"
              >
                {tasksLoading ? (
                  <p className="text-sm text-muted-foreground">Carregando tarefas…</p>
                ) : tasksError ? (
                  <QueryError
                    message="Não foi possível carregar as tarefas deste projeto."
                    onRetry={() => void refetchTasks()}
                  />
                ) : tasks.length === 0 ? (
                  <div className="rounded-xl border border-dashed py-16 text-center">
                    <p className="text-sm font-medium text-foreground">
                      Nenhuma tarefa neste projeto
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Use “Nova tarefa” para adicionar a primeira.
                    </p>
                  </div>
                ) : (
                  <TaskListView tasks={tasks} onSelect={(task) => setOpenTaskId(task.id)} />
                )}
              </TabsContent>

              <TabsContent
                value="kanban"
                className="mt-0 h-full overflow-hidden px-4 py-5 sm:px-6 lg:px-8 lg:py-6"
              >
                {tasksError ? (
                  <QueryError
                    message="Não foi possível carregar as tarefas deste projeto."
                    onRetry={() => void refetchTasks()}
                  />
                ) : (
                  <TaskKanbanView
                    tasks={tasks}
                    onSelect={(task) => setOpenTaskId(task.id)}
                  />
                )}
              </TabsContent>
            </div>
          </Tabs>
        )}
      </main>

      <TaskDetailSheet
        task={openTask}
        onOpenChange={(open) => {
          if (!open) {
            setOpenTaskId(null)
          }
        }}
      />
    </div>
  )
}
