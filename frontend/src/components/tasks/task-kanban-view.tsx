import { CalendarIcon } from 'lucide-react'
import { TagBadge } from '@/components/tasks/tag-badge'
import { formatDeadline } from '@/lib/format'
import { STATUS_META, STATUS_ORDER } from '@/lib/status'
import { cn } from '@/lib/utils'
import type { Task, TaskStatus } from '@/types'

const COLUMN_TINT: Record<TaskStatus, string> = {
  not_started: 'bg-slate-50/80',
  in_progress: 'bg-blue-50/60',
  done: 'bg-emerald-50/60',
  cancelled: 'bg-rose-50/60',
}

interface TaskKanbanViewProps {
  tasks: Task[]
  onSelect: (task: Task) => void
}

export function TaskKanbanView({ tasks, onSelect }: TaskKanbanViewProps) {
  return (
    <div className="flex h-full gap-4 overflow-x-auto pb-2">
      {STATUS_ORDER.map((status) => {
        const meta = STATUS_META[status]
        const columnTasks = tasks.filter((task) => task.status === status)

        return (
          <div
            key={status}
            className={cn(
              'flex w-72 shrink-0 flex-col rounded-xl border border-black/5',
              COLUMN_TINT[status],
            )}
          >
            <div className="flex items-center justify-between px-3 py-3">
              <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <span className={cn('size-2 rounded-full', meta.dot)} />
                {meta.label}
              </span>
              <span className="rounded-full bg-background/70 px-1.5 text-xs font-medium text-muted-foreground">
                {columnTasks.length}
              </span>
            </div>

            <div className="flex-1 space-y-2.5 overflow-y-auto px-2.5 pb-3">
              {columnTasks.map((task) => {
                const deadline = formatDeadline(task.deadline)
                return (
                  <button
                    key={task.id}
                    type="button"
                    onClick={() => onSelect(task)}
                    aria-label={`Abrir tarefa: ${task.title}`}
                    className="w-full rounded-lg border bg-card p-3 text-left shadow-sm transition-shadow hover:shadow-card focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
                  >
                    <p
                      className={cn(
                        'text-sm font-semibold text-foreground',
                        status === 'cancelled' && 'text-muted-foreground line-through',
                      )}
                    >
                      {task.title}
                    </p>
                    {task.short_description && (
                      <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                        {task.short_description}
                      </p>
                    )}
                    <div className="mt-2.5 flex items-center justify-between gap-2">
                      <span className="min-w-0">
                        {task.tags[0] && <TagBadge tag={task.tags[0]} />}
                      </span>
                      {deadline && (
                        <span className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground">
                          <CalendarIcon className="size-3" />
                          {deadline}
                        </span>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
