import type { ComponentProps, ReactNode } from 'react'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface AuthFieldProps extends ComponentProps<'input'> {
  label: string
  error?: string
  labelAside?: ReactNode
}

/** Uppercase label + shadcn Input + inline validation error. */
export function AuthField({ label, error, labelAside, id, className, ...props }: AuthFieldProps) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label
          htmlFor={id}
          className="text-xs font-semibold tracking-wide text-muted-foreground uppercase"
        >
          {label}
        </label>
        {labelAside}
      </div>
      <Input
        id={id}
        className={cn('h-10', className)}
        aria-invalid={error ? true : undefined}
        {...props}
      />
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}
