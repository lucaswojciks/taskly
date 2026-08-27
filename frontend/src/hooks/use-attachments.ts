import { useMutation, useQueryClient } from '@tanstack/react-query'
import { projectTasksQueryKey } from '@/hooks/use-tasks'
import { deleteAttachment, uploadAttachment } from '@/lib/attachments-api'

interface UploadVariables {
  file: File
  onProgress?: (percent: number) => void
}

export function useUploadAttachment(projectId: string, taskId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, onProgress }: UploadVariables) =>
      uploadAttachment(projectId, taskId, file, onProgress),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectTasksQueryKey(projectId) })
    },
  })
}

export function useDeleteAttachment(projectId: string, taskId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (attachmentId: string) =>
      deleteAttachment(projectId, taskId, attachmentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectTasksQueryKey(projectId) })
    },
  })
}
