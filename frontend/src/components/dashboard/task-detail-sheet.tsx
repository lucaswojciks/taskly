import {
  type ChangeEvent,
  type ReactNode,
  useEffect,
  useRef,
  useState,
} from 'react'
import { isAxiosError } from 'axios'
import {
  CheckIcon,
  FileTextIcon,
  Loader2Icon,
  PaperclipIcon,
  Trash2Icon,
} from 'lucide-react'
import { toast } from 'sonner'
import { TagMultiSelect, type TagSelection } from '@/components/tasks/tag-multi-select'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import { useDeleteAttachment, useUploadAttachment } from '@/hooks/use-attachments'
import { useDeleteTask, useUpdateTask } from '@/hooks/use-task-mutations'
import { useCreateTag, useProjectTags } from '@/hooks/use-tags'
import { datetimeLocalToIso, isoToDatetimeLocal } from '@/lib/datetime'
import { STATUS_META, STATUS_ORDER } from '@/lib/status'
import type { UpdateTaskPayload } from '@/lib/tasks-api'
import { cn } from '@/lib/utils'
import type { Attachment, Task, TaskStatus } from '@/types'

interface TaskDetailSheetProps {
  task: Task | null
  onOpenChange: (open: boolean) => void
}

export function TaskDetailSheet({ task, onOpenChange }: TaskDetailSheetProps) {
  return (
    <Sheet open={task !== null} onOpenChange={onOpenChange}>
      <SheetContent className="flex w-full flex-col gap-0 p-0 sm:max-w-md">
        <SheetHeader className="sr-only">
          <SheetTitle>Detalhe da tarefa</SheetTitle>
          <SheetDescription>
            Edite os campos da tarefa. As alterações são salvas automaticamente.
          </SheetDescription>
        </SheetHeader>
        {task && (
          <TaskDetailPanel
            key={task.id}
            task={task}
            onClose={() => onOpenChange(false)}
          />
        )}
      </SheetContent>
    </Sheet>
  )
}

type SaveState = 'idle' | 'saving' | 'saved'

function TaskDetailPanel({ task, onClose }: { task: Task; onClose: () => void }) {
  const projectId = task.project_id

  const [title, setTitle] = useState(task.title)
  const [shortDescription, setShortDescription] = useState(task.short_description)
  const [fullDescription, setFullDescription] = useState(task.full_description)
  const [status, setStatus] = useState<TaskStatus>(task.status)
  const [deadlineLocal, setDeadlineLocal] = useState(isoToDatetimeLocal(task.deadline))
  const [tags, setTags] = useState<TagSelection[]>(
    task.tags.map((tag) => ({ kind: 'existing', id: tag.id, name: tag.name })),
  )

  const [saveState, setSaveState] = useState<SaveState>('idle')
  const [uploadPercent, setUploadPercent] = useState<number | null>(null)
  const [confirmingAttachmentId, setConfirmingAttachmentId] = useState<string | null>(
    null,
  )

  const savedTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const update = useUpdateTask(projectId, task.id)
  const removeTask = useDeleteTask(projectId)
  const createTag = useCreateTag(projectId)
  const upload = useUploadAttachment(projectId, task.id)
  const removeAttachment = useDeleteAttachment(projectId, task.id)
  const { data: availableTags = [] } = useProjectTags(projectId)

  useEffect(() => () => clearTimeout(savedTimer.current), [])

  function flashSaved() {
    setSaveState('saved')
    clearTimeout(savedTimer.current)
    savedTimer.current = setTimeout(() => setSaveState('idle'), 1500)
  }

  async function patch(payload: UpdateTaskPayload): Promise<Task | null> {
    setSaveState('saving')
    try {
      const result = await update.mutateAsync(payload)
      flashSaved()
      return result
    } catch {
      setSaveState('idle')
      toast.error('Não foi possível salvar as alterações.')
      return null
    }
  }

  function commitTitle() {
    const next = title.trim()
    if (!next) {
      setTitle(task.title)
    } else if (next !== task.title) {
      void patch({ title: next })
    }
  }

  function commitShortDescription() {
    const next = shortDescription.trim()
    if (!next) {
      setShortDescription(task.short_description)
    } else if (next !== task.short_description) {
      void patch({ short_description: next })
    }
  }

  function commitFullDescription() {
    if (fullDescription !== task.full_description) {
      void patch({ full_description: fullDescription })
    }
  }

  function changeStatus(next: string) {
    setStatus(next as TaskStatus)
    void patch({ status: next as TaskStatus })
  }

  function changeDeadline(event: ChangeEvent<HTMLInputElement>) {
    const value = event.target.value
    setDeadlineLocal(value)
    if (value === '' || value.length >= 16) {
      void patch({ deadline: value ? datetimeLocalToIso(value) : null })
    }
  }

  function clearDeadline() {
    setDeadlineLocal('')
    void patch({ deadline: null })
  }

  async function changeTags(next: TagSelection[]) {
    setTags(next)
    setSaveState('saving')
    try {
      const tagIds: string[] = []
      for (const selection of next) {
        if (selection.kind === 'existing') {
          tagIds.push(selection.id)
        } else {
          tagIds.push((await createTag.mutateAsync(selection.name)).id)
        }
      }
      const result = await update.mutateAsync({ tag_ids: tagIds })
      setTags(
        result.tags.map((tag) => ({ kind: 'existing', id: tag.id, name: tag.name })),
      )
      flashSaved()
    } catch {
      setSaveState('idle')
      toast.error('Não foi possível atualizar as tags.')
      setTags(
        task.tags.map((tag) => ({ kind: 'existing', id: tag.id, name: tag.name })),
      )
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) {
      return
    }
    setUploadPercent(0)
    try {
      await upload.mutateAsync({ file, onProgress: setUploadPercent })
      toast.success('Anexo adicionado.')
    } catch (error) {
      toast.error(attachmentErrorMessage(error))
    } finally {
      setUploadPercent(null)
    }
  }

  async function handleDeleteAttachment(attachmentId: string) {
    try {
      await removeAttachment.mutateAsync(attachmentId)
      toast.success('Anexo removido.')
    } catch {
      toast.error('Não foi possível remover o anexo.')
    } finally {
      setConfirmingAttachmentId(null)
    }
  }

  async function handleDeleteTask() {
    try {
      await removeTask.mutateAsync(task.id)
      toast.success('Tarefa removida.')
      onClose()
    } catch {
      toast.error('Não foi possível remover a tarefa.')
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b py-3.5 pr-14 pl-5">
        <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          Detalhe da tarefa
        </p>
        <SaveIndicator state={saveState} />
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto px-4 py-5 sm:px-5">
        <Section label="Título" htmlFor="task-title">
          <input
            id="task-title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            onBlur={commitTitle}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.currentTarget.blur()
              }
            }}
            maxLength={200}
            className={cn(
              'w-full rounded-md border border-transparent bg-transparent px-2 py-1 text-lg font-bold text-foreground outline-none',
              'hover:border-input focus:border-ring focus:ring-[3px] focus:ring-ring/40',
              task.status === 'cancelled' && 'text-muted-foreground line-through',
            )}
          />
        </Section>

        <Section label="Resumo" htmlFor="task-short">
          <Input
            id="task-short"
            value={shortDescription}
            onChange={(event) => setShortDescription(event.target.value)}
            onBlur={commitShortDescription}
            maxLength={500}
            className="h-10"
          />
        </Section>

        <Section label="Descrição completa" htmlFor="task-full">
          <Textarea
            id="task-full"
            value={fullDescription}
            onChange={(event) => setFullDescription(event.target.value)}
            onBlur={commitFullDescription}
            rows={4}
            maxLength={20000}
            placeholder="Sem descrição"
          />
        </Section>

        <Section label="Status" htmlFor="task-status">
          <Select value={status} onValueChange={changeStatus}>
            <SelectTrigger id="task-status" className="h-10 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {STATUS_ORDER.map((option) => (
                <SelectItem key={option} value={option}>
                  <span className="flex items-center gap-2">
                    <span
                      className={cn('size-2 rounded-full', STATUS_META[option].dot)}
                    />
                    {STATUS_META[option].label}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Section>

        <Section label="Prazo" htmlFor="task-deadline">
          <div className="flex items-center gap-2">
            <Input
              id="task-deadline"
              type="datetime-local"
              value={deadlineLocal}
              onChange={changeDeadline}
              className="h-10 flex-1"
            />
            {deadlineLocal && (
              <Button type="button" variant="ghost" size="sm" onClick={clearDeadline}>
                Limpar
              </Button>
            )}
          </div>
        </Section>

        <Section label="Tags">
          <TagMultiSelect
            availableTags={availableTags}
            value={tags}
            onChange={(next) => void changeTags(next)}
          />
        </Section>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              Anexos ({task.attachments.length})
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={uploadPercent !== null}
              onClick={() => fileInputRef.current?.click()}
            >
              <PaperclipIcon className="size-3.5" />
              Adicionar
            </Button>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            aria-label="Enviar arquivo como anexo"
            className="hidden"
            onChange={handleFileChange}
          />

          {uploadPercent !== null && (
            <div className="space-y-1">
              <div
                role="progressbar"
                aria-label="Enviando anexo"
                aria-valuenow={uploadPercent}
                aria-valuemin={0}
                aria-valuemax={100}
                className="h-1.5 overflow-hidden rounded-full bg-muted"
              >
                <div
                  className="h-full rounded-full bg-brand-500 transition-all"
                  style={{ width: `${uploadPercent}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Enviando… {uploadPercent}%
              </p>
            </div>
          )}

          {task.attachments.length === 0 && uploadPercent === null && (
            <p className="text-xs text-muted-foreground">Nenhum anexo ainda.</p>
          )}

          <ul className="space-y-2">
            {task.attachments.map((attachment) => (
              <AttachmentRow
                key={attachment.id}
                attachment={attachment}
                confirming={confirmingAttachmentId === attachment.id}
                onAskConfirm={() => setConfirmingAttachmentId(attachment.id)}
                onCancelConfirm={() => setConfirmingAttachmentId(null)}
                onConfirmDelete={() => void handleDeleteAttachment(attachment.id)}
              />
            ))}
          </ul>
        </div>
      </div>

      <div className="border-t px-5 py-3">
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              className="w-full text-destructive hover:bg-destructive/10 hover:text-destructive"
            >
              <Trash2Icon className="size-4" />
              Remover tarefa
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Remover esta tarefa?</AlertDialogTitle>
              <AlertDialogDescription>
                “{task.title}” e seus anexos serão removidos permanentemente. Esta
                ação não pode ser desfeita.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancelar</AlertDialogCancel>
              <AlertDialogAction
                className="bg-destructive text-white hover:bg-destructive/90"
                onClick={() => void handleDeleteTask()}
              >
                Remover
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  )
}

function Section({
  label,
  htmlFor,
  children,
}: {
  label: string
  htmlFor?: string
  children: ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <label
        htmlFor={htmlFor}
        className="block text-xs font-semibold tracking-wide text-muted-foreground uppercase"
      >
        {label}
      </label>
      {children}
    </div>
  )
}

function SaveIndicator({ state }: { state: SaveState }) {
  if (state === 'saving') {
    return (
      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Loader2Icon className="size-3 animate-spin" />
        Salvando…
      </span>
    )
  }
  if (state === 'saved') {
    return (
      <span className="flex items-center gap-1.5 text-xs text-status-done">
        <CheckIcon className="size-3" />
        Salvo
      </span>
    )
  }
  return null
}

function AttachmentRow({
  attachment,
  confirming,
  onAskConfirm,
  onCancelConfirm,
  onConfirmDelete,
}: {
  attachment: Attachment
  confirming: boolean
  onAskConfirm: () => void
  onCancelConfirm: () => void
  onConfirmDelete: () => void
}) {
  const isImage = attachment.content_type.startsWith('image/')

  return (
    <li className="flex items-center gap-3 rounded-lg border p-2">
      {isImage ? (
        <img
          src={attachment.url}
          alt=""
          className="size-10 shrink-0 rounded object-cover"
        />
      ) : (
        <span className="flex size-10 shrink-0 items-center justify-center rounded bg-muted text-muted-foreground">
          <FileTextIcon className="size-5" />
        </span>
      )}

      <a
        href={attachment.url}
        target="_blank"
        rel="noreferrer"
        className="min-w-0 flex-1 truncate text-sm font-medium text-brand-700 hover:underline"
      >
        {attachment.file_name}
      </a>

      {confirming ? (
        <div className="flex shrink-0 items-center gap-1">
          <Button type="button" variant="ghost" size="xs" onClick={onCancelConfirm}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant="destructive"
            size="xs"
            onClick={onConfirmDelete}
          >
            Remover
          </Button>
        </div>
      ) : (
        <button
          type="button"
          onClick={onAskConfirm}
          aria-label={`Remover ${attachment.file_name}`}
          className="shrink-0 rounded p-1 text-muted-foreground transition-colors hover:text-destructive"
        >
          <Trash2Icon className="size-4" />
        </button>
      )}
    </li>
  )
}

function attachmentErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    switch (error.response?.status) {
      case 422:
        return 'Tipo de arquivo não suportado. Envie JPEG, PNG, WebP ou PDF.'
      case 413:
        return 'Arquivo muito grande. O limite é 10 MB.'
      case 502:
        return 'Falha ao armazenar o arquivo. Tente novamente.'
    }
  }
  return 'Não foi possível enviar o anexo.'
}
