import { api, type ListParams } from '@/lib/api'
import type { Task } from '@/types'

/** GET /projects/{id}/tasks — plain JSON array, accepts ?limit=&offset=. */
export async function listProjectTasks(
  projectId: string,
  params?: ListParams,
): Promise<Task[]> {
  const { data } = await api.get<Task[]>(`/projects/${projectId}/tasks`, { params })
  return data
}
