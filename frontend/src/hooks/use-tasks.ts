import { useQuery } from '@tanstack/react-query'
import { listProjectTasks } from '@/lib/tasks-api'
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
