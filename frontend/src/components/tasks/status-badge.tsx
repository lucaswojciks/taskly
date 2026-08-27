import { STATUS_META } from '@/lib/status'
import { cn } from '@/lib/utils'
import type { TaskStatus } from '@/types'

export function StatusBadge({
  status,
  className,
}: {
  status: TaskStatus
  className?: string
}) {
  const meta = STATUS_META[status]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap',
        meta.badge,
        className,
      )}
    >
      <span className={cn('size-1.5 rounded-full', meta.dot)} />
      {meta.label}
    </span>
  )
}
