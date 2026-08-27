import { useState } from 'react'
import { FolderPlusIcon, LayoutGridIcon, ListIcon } from 'lucide-react'
import { DashboardSidebar } from '@/components/dashboard/dashboard-sidebar'
import { NewProjectDialog } from '@/components/dashboard/new-project-dialog'
import { NewTaskDialog } from '@/components/dashboard/new-task-dialog'
import { StatusSummary } from '@/components/dashboard/status-summary'
import { TaskDetailSheet } from '@/components/dashboard/task-detail-sheet'
import { TaskListView } from '@/components/tasks/task-list-view'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useProjects } from '@/hooks/use-projects'
import { useProjectTasks } from '@/hooks/use-tasks'
import type { Task } from '@/types'

type View = 'list' | 'kanban'

export function DashboardPage() {
  const { data: projects = [], isLoading: projectsLoading } = useProjects()

  const [pickedProjectId, setPickedProjectId] = useState<string | null>(null)
  const selectedProjectId = pickedProjectId ?? projects[0]?.id ?? null
  const selectedProject =
    projects.find((project) => project.id === selectedProjectId) ?? null

  const { data: tasks = [], isLoading: tasksLoading } =
    useProjectTasks(selectedProjectId)

  const [view, setView] = useState<View>('list')
  const [openTask, setOpenTask] = useState<Task | null>(null)

  const doneCount = tasks.filter((task) => task.status === 'done').length

  return (
    <div className="flex h-svh overflow-hidden bg-background">
      <DashboardSidebar
        selectedProjectId={selectedProjectId}
        onSelectProject={setPickedProjectId}
      />

      <main className="flex flex-1 flex-col overflow-hidden">
        {projectsLoading ? (
          <div className="grid flex-1 place-items-center text-sm text-muted-foreground">
            Carregando…
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
            <header className="flex items-center justify-between gap-4 border-b px-8 py-4">
              <div className="min-w-0">
                <h1 className="truncate text-xl font-bold tracking-tight text-foreground">
                  {selectedProject?.name}
                </h1>
                <p className="text-xs text-muted-foreground">
                  {tasks.length} {tasks.length === 1 ? 'tarefa' : 'tarefas'}
                  {' · '}
                  {doneCount} {doneCount === 1 ? 'concluída' : 'concluídas'}
                </p>
              </div>

              <div className="flex shrink-0 items-center gap-3">
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
                <NewTaskDialog />
              </div>
            </header>

            <div className="border-b px-8 py-4">
              <StatusSummary tasks={tasks} />
            </div>

            <div className="flex-1 overflow-y-auto px-8 py-6">
              <TabsContent value="list" className="mt-0">
                {tasksLoading ? (
                  <p className="text-sm text-muted-foreground">Carregando tarefas…</p>
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
                  <TaskListView tasks={tasks} onSelect={setOpenTask} />
                )}
              </TabsContent>

              <TabsContent value="kanban" className="mt-0">
                <div className="grid place-items-center py-20 text-sm text-muted-foreground">
                  A visão Kanban chega em breve.
                </div>
              </TabsContent>
            </div>
          </Tabs>
        )}
      </main>

      <TaskDetailSheet
        task={openTask}
        onOpenChange={(open) => {
          if (!open) {
            setOpenTask(null)
          }
        }}
      />
    </div>
  )
}
