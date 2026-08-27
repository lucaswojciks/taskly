import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { type CreateTaskPayload, createProjectTask, listProjectTasks } from '@/lib/tasks-api'
import type { Task } from '@/types'

export function projectTasksQueryKey(projectId: string | null) {
  return ['projects', projectId, 'tasks'] as const
}

export function useProjectTasks(projectId: string | null) {
  return useQuery<Task[]>({
    queryKey: projectTasksQueryKey(projectId),
    queryFn: () => listProjectTasks(projectId as string, { limit: 200 }),
    enabled: projectId !== null,
  })
}

export function useCreateTask(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateTaskPayload) => createProjectTask(projectId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: projectTasksQueryKey(projectId) })
    },
  })
}
