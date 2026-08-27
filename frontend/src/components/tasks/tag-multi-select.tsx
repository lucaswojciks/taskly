import { type KeyboardEvent, useState } from 'react'
import { PlusIcon, XIcon } from 'lucide-react'
import { tagClasses } from '@/lib/colors'
import { cn } from '@/lib/utils'
import type { Tag } from '@/types'

export type TagSelection =
  | { kind: 'existing'; id: string; name: string }
  | { kind: 'new'; name: string }

interface TagMultiSelectProps {
  availableTags: Tag[]
  value: TagSelection[]
  onChange: (value: TagSelection[]) => void
}

/**
 * Simple tag picker: pick from the project's existing tags or type a new name
 * (Enter, or the "Criar …" chip) to queue a brand-new tag for creation.
 */
export function TagMultiSelect({ availableTags, value, onChange }: TagMultiSelectProps) {
  const [input, setInput] = useState('')

  const selectedNames = new Set(value.map((item) => item.name.toLowerCase()))
  const query = input.trim().toLowerCase()

  const suggestions = availableTags.filter(
    (tag) => !selectedNames.has(tag.name.toLowerCase()) && tag.name.toLowerCase().includes(query),
  )
  const canCreate =
    query.length > 0 &&
    !selectedNames.has(query) &&
    !availableTags.some((tag) => tag.name.toLowerCase() === query)

  function add(name: string) {
    const trimmed = name.trim()
    if (!trimmed || selectedNames.has(trimmed.toLowerCase())) {
      setInput('')
      return
    }
    const existing = availableTags.find(
      (tag) => tag.name.toLowerCase() === trimmed.toLowerCase(),
    )
    onChange([
      ...value,
      existing
        ? { kind: 'existing', id: existing.id, name: existing.name }
        : { kind: 'new', name: trimmed },
    ])
    setInput('')
  }

  function remove(name: string) {
    onChange(value.filter((item) => item.name !== name))
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') {
      event.preventDefault()
      add(input)
    } else if (event.key === 'Backspace' && input === '' && value.length > 0) {
      onChange(value.slice(0, -1))
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex min-h-10 flex-wrap items-center gap-1.5 rounded-md border border-input px-2 py-1.5 focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/40">
        {value.map((item) => (
          <span
            key={item.name}
            className={cn(
              'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium',
              tagClasses(item.name),
            )}
          >
            {item.name}
            {item.kind === 'new' && <span className="opacity-60">(nova)</span>}
            <button
              type="button"
              onClick={() => remove(item.name)}
              aria-label={`Remover ${item.name}`}
              className="rounded-full transition-colors hover:bg-black/10"
            >
              <XIcon className="size-3" />
            </button>
          </span>
        ))}
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Adicionar tag"
          placeholder={value.length === 0 ? 'Digite e pressione Enter' : ''}
          className="min-w-24 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </div>

      {(suggestions.length > 0 || canCreate) && (
        <div className="flex flex-wrap gap-1.5">
          {suggestions.map((tag) => (
            <button
              key={tag.id}
              type="button"
              onClick={() => add(tag.name)}
              className="inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs text-muted-foreground transition-colors hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:outline-none"
            >
              <PlusIcon className="size-3" />
              {tag.name}
            </button>
          ))}
          {canCreate && (
            <button
              type="button"
              onClick={() => add(input)}
              className="inline-flex items-center gap-1 rounded-md border border-dashed px-2 py-0.5 text-xs font-medium text-brand-700 transition-colors hover:bg-brand-50"
            >
              <PlusIcon className="size-3" />
              Criar “{input.trim()}”
            </button>
          )}
        </div>
      )}
    </div>
  )
}
