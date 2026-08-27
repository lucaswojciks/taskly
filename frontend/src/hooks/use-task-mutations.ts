import { useMutation, useQueryClient } from '@tanstack/react-query'
import { projectTasksQueryKey } from '@/hooks/use-tasks'
import {
  type UpdateTaskPayload,
  deleteProjectTask,
  updateProjectTask,
} from '@/lib/tasks-api'
import type { Task } from '@/types'

export function useUpdateTask(projectId: string, taskId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (patch: UpdateTaskPayload) =>
      updateProjectTask(projectId, taskId, patch),
    onSuccess: (updated) => {
      queryClient.setQueryData<Task[]>(projectTasksQueryKey(projectId), (current) =>
        current?.map((task) => (task.id === updated.id ? updated : task)),
      )
    },
  })
}

export function useDeleteTask(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (taskId: string) => deleteProjectTask(projectId, taskId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectTasksQueryKey(projectId) })
    },
  })
}
