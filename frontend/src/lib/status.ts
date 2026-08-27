import type { TaskStatus } from '@/types'

export interface StatusMeta {
  label: string
  /** badge pill classes (soft bg + text) */
  badge: string
  /** solid dot / accent bg class */
  dot: string
  /** accent text class */
  text: string
}

export const STATUS_META: Record<TaskStatus, StatusMeta> = {
  not_started: {
    label: 'Não iniciada',
    badge: 'bg-status-neutral-soft text-status-neutral',
    dot: 'bg-status-neutral',
    text: 'text-status-neutral',
  },
  in_progress: {
    label: 'Em andamento',
    badge: 'bg-status-progress-soft text-status-progress',
    dot: 'bg-status-progress',
    text: 'text-status-progress',
  },
  done: {
    label: 'Concluída',
    badge: 'bg-status-done-soft text-status-done',
    dot: 'bg-status-done',
    text: 'text-status-done',
  },
  cancelled: {
    label: 'Cancelada',
    badge: 'bg-status-cancelled-soft text-status-cancelled',
    dot: 'bg-status-cancelled',
    text: 'text-status-cancelled',
  },
}

/** Status order for the Kanban columns / grouped views. */
export const STATUS_ORDER: TaskStatus[] = [
  'not_started',
  'in_progress',
  'done',
  'cancelled',
]
