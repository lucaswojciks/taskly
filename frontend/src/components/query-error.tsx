import { RefreshCwIcon, TriangleAlertIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface QueryErrorProps {
  message: string
  onRetry: () => void
  className?: string
}

/** Friendly fallback for a failed query, with a "try again" action. */
export function QueryError({ message, onRetry, className }: QueryErrorProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center gap-3 rounded-xl border border-dashed p-8 text-center',
        className,
      )}
    >
      <TriangleAlertIcon className="size-8 text-muted-foreground" />
      <p className="text-sm font-medium text-foreground">{message}</p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RefreshCwIcon className="size-3.5" />
        Tentar novamente
      </Button>
    </div>
  )
}
