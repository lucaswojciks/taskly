import { type ReactNode, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { PlusIcon } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'
import { TagMultiSelect, type TagSelection } from '@/components/tasks/tag-multi-select'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useCreateTask } from '@/hooks/use-tasks'
import { useCreateTag, useProjectTags } from '@/hooks/use-tags'

const schema = z.object({
  title: z.string().trim().min(1, 'Informe o título').max(200, 'Máximo de 200 caracteres'),
  shortDescription: z
    .string()
    .trim()
    .min(1, 'Informe a descrição curta')
    .max(500, 'Máximo de 500 caracteres'),
  fullDescription: z.string().max(20000, 'Máximo de 20000 caracteres').optional(),
  deadline: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

/** datetime-local ("2026-09-01T18:00", local time) -> ISO string with timezone. */
function toIsoWithTimezone(localValue: string): string {
  return new Date(localValue).toISOString()
}

function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string
  hint?: string
  error?: string
  children: ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          {label}
        </span>
        {hint && <span className="text-xs text-muted-foreground/70">{hint}</span>}
      </div>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}

export function NewTaskDialog({ projectId }: { projectId: string }) {
  const [open, setOpen] = useState(false)
  const [tags, setTags] = useState<TagSelection[]>([])

  const { data: availableTags = [] } = useProjectTags(open ? projectId : null)
  const createTag = useCreateTag(projectId)
  const createTask = useCreateTask(projectId)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  function resetForm() {
    reset()
    setTags([])
  }

  const onSubmit = handleSubmit(async (values) => {
    try {
      const tagIds: string[] = []
      for (const selection of tags) {
        if (selection.kind === 'existing') {
          tagIds.push(selection.id)
        } else {
          const created = await createTag.mutateAsync(selection.name)
          tagIds.push(created.id)
        }
      }

      await createTask.mutateAsync({
        title: values.title,
        short_description: values.shortDescription,
        full_description: values.fullDescription?.trim() || undefined,
        deadline: values.deadline ? toIsoWithTimezone(values.deadline) : undefined,
        tag_ids: tagIds,
      })

      toast.success('Tarefa criada.')
      setOpen(false)
      resetForm()
    } catch {
      toast.error('Não foi possível criar a tarefa.')
    }
  })

  const pending = createTask.isPending || createTag.isPending

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) {
          resetForm()
        }
      }}
    >
      <DialogTrigger asChild>
        <Button className="bg-gradient-to-r from-brand-500 to-brand-700 hover:from-brand-600 hover:to-brand-800">
          <PlusIcon className="size-4" />
          Nova tarefa
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nova tarefa</DialogTitle>
          <DialogDescription>Adicione uma tarefa a este projeto.</DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Título" error={errors.title?.message}>
            <Input
              autoFocus
              maxLength={200}
              className="h-10"
              {...register('title')}
              aria-invalid={errors.title ? true : undefined}
            />
          </Field>

          <Field label="Descrição curta" error={errors.shortDescription?.message}>
            <Input
              maxLength={500}
              className="h-10"
              {...register('shortDescription')}
              aria-invalid={errors.shortDescription ? true : undefined}
            />
          </Field>

          <Field label="Descrição completa" hint="opcional" error={errors.fullDescription?.message}>
            <Textarea rows={3} maxLength={20000} {...register('fullDescription')} />
          </Field>

          <Field label="Prazo" hint="opcional">
            <Input type="datetime-local" className="h-10" {...register('deadline')} />
          </Field>

          <Field label="Tags" hint="opcional">
            <TagMultiSelect availableTags={availableTags} value={tags} onChange={setTags} />
          </Field>

          <DialogFooter>
            <Button
              type="submit"
              disabled={pending}
              className="bg-gradient-to-r from-brand-500 to-brand-700 hover:from-brand-600 hover:to-brand-800"
            >
              {pending ? 'Criando…' : 'Criar tarefa'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
