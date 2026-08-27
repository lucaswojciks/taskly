import { type FormEvent, type ReactNode, useState } from 'react'
import { toast } from 'sonner'
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
import { useCreateProject } from '@/hooks/use-projects'

interface NewProjectDialogProps {
  children: ReactNode
  onCreated?: (projectId: string) => void
}

export function NewProjectDialog({ children, onCreated }: NewProjectDialogProps) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const mutation = useCreateProject()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed || mutation.isPending) {
      return
    }
    mutation.mutate(trimmed, {
      onSuccess: (project) => {
        toast.success('Projeto criado.')
        setName('')
        setOpen(false)
        onCreated?.(project.id)
      },
      onError: () => toast.error('Não foi possível criar o projeto.'),
    })
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) {
          setName('')
        }
      }}
    >
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Novo projeto</DialogTitle>
          <DialogDescription>Dê um nome ao seu projeto.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            autoFocus
            aria-label="Nome do projeto"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Ex.: Taskly App"
            maxLength={120}
            className="h-10"
          />
          <DialogFooter>
            <Button
              type="submit"
              disabled={mutation.isPending || name.trim().length === 0}
              className="bg-gradient-to-r from-brand-500 to-brand-700 hover:from-brand-600 hover:to-brand-800"
            >
              {mutation.isPending ? 'Criando…' : 'Criar projeto'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
