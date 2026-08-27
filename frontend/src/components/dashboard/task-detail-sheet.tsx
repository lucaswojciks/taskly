import { StatusBadge } from '@/components/tasks/status-badge'
import { TagBadge } from '@/components/tasks/tag-badge'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import type { Task } from '@/types'

interface TaskDetailSheetProps {
  task: Task | null
  onOpenChange: (open: boolean) => void
}

/** Placeholder — the full editable detail lands in a later step. */
export function TaskDetailSheet({ task, onOpenChange }: TaskDetailSheetProps) {
  return (
    <Sheet open={task !== null} onOpenChange={onOpenChange}>
      <SheetContent className="w-full gap-6 sm:max-w-md">
        {task && (
          <>
            <SheetHeader className="gap-2">
              <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                Detalhe da tarefa
              </p>
              <SheetTitle className="text-lg leading-snug">{task.title}</SheetTitle>
              {task.short_description && (
                <SheetDescription>{task.short_description}</SheetDescription>
              )}
            </SheetHeader>

            <div className="space-y-4 px-4">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge status={task.status} />
                {task.tags.map((tag) => (
                  <TagBadge key={tag.id} tag={tag} />
                ))}
              </div>
              <p className="text-sm text-muted-foreground">
                A edição completa da tarefa (descrição, prazo, status, tags e anexos)
                chega no próximo passo.
              </p>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
