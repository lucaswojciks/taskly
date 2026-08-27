import { Fragment } from 'react'
import { cn } from '@/lib/utils'
import type { Task, TaskStatus } from '@/types'

type SummaryKey = TaskStatus | 'total'

const ITEMS: { key: SummaryKey; label: string; className: string }[] = [
  { key: 'total', label: 'Total', className: 'text-foreground' },
  { key: 'in_progress', label: 'Em andamento', className: 'text-status-progress' },
  { key: 'done', label: 'Concluídas', className: 'text-status-done' },
  { key: 'not_started', label: 'Não iniciadas', className: 'text-status-neutral' },
]

export function StatusSummary({ tasks }: { tasks: Task[] }) {
  const countFor = (key: SummaryKey) =>
    key === 'total' ? tasks.length : tasks.filter((task) => task.status === key).length

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      {ITEMS.map((item, index) => (
        <Fragment key={item.key}>
          {index > 0 && <span className="text-muted-foreground/30">·</span>}
          <span className="flex items-baseline gap-1.5">
            <span className={cn('text-lg font-bold', item.className)}>
              {countFor(item.key)}
            </span>
            <span className="text-muted-foreground">{item.label}</span>
          </span>
        </Fragment>
      ))}
    </div>
  )
}
