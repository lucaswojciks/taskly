import type { Tag } from '@/types'
import { tagClasses } from '@/lib/colors'
import { cn } from '@/lib/utils'

export function TagBadge({ tag, className }: { tag: Tag; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium whitespace-nowrap',
        tagClasses(tag.name),
        className,
      )}
    >
      {tag.name}
    </span>
  )
}
