import { CalendarIcon, CheckIcon, ChevronRightIcon } from 'lucide-react'
import { StatusBadge } from '@/components/tasks/status-badge'
import { TagBadge } from '@/components/tasks/tag-badge'
import { formatDeadline } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { Task } from '@/types'

interface TaskListViewProps {
  tasks: Task[]
  onSelect: (task: Task) => void
}

export function TaskListView({ tasks, onSelect }: TaskListViewProps) {
  return (
    <ul className="space-y-2.5">
      {tasks.map((task) => {
        const done = task.status === 'done'
        const cancelled = task.status === 'cancelled'
        const deadline = formatDeadline(task.deadline)

        return (
          <li key={task.id}>
            <button
              type="button"
              onClick={() => onSelect(task)}
              className="flex w-full items-center gap-4 rounded-xl border bg-card px-5 py-4 text-left shadow-card transition-colors hover:border-brand-200 hover:bg-brand-50/40"
            >
              <span
                className={cn(
                  'flex size-5 shrink-0 items-center justify-center rounded-full border-2',
                  done && 'border-status-done bg-status-done text-white',
                  !done && cancelled && 'border-status-cancelled/40',
                  !done && !cancelled && 'border-muted-foreground/25',
                )}
              >
                {done && <CheckIcon className="size-3" strokeWidth={3} />}
              </span>

              <div className="min-w-0 flex-1">
                <p
                  className={cn(
                    'truncate text-sm font-semibold text-foreground',
                    cancelled && 'text-muted-foreground line-through',
                  )}
                >
                  {task.title}
                </p>
                {task.short_description && (
                  <p className="truncate text-xs text-muted-foreground">
                    {task.short_description}
                  </p>
                )}
              </div>

              <div className="flex shrink-0 items-center gap-2.5">
                {task.tags[0] && (
                  <TagBadge tag={task.tags[0]} className="hidden sm:inline-flex" />
                )}
                <StatusBadge status={task.status} />
                {deadline && (
                  <span className="hidden items-center gap-1 text-xs text-muted-foreground md:flex">
                    <CalendarIcon className="size-3.5" />
                    {deadline}
                  </span>
                )}
                <ChevronRightIcon className="size-4 text-muted-foreground/40" />
              </div>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
